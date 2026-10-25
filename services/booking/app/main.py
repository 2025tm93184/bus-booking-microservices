
import hashlib
import json
import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.models import Booking, IdempotencyRecord
from app.schemas import BookingCreate, BookingResponse
from app.service_clients import (
    reserve_seat,
    process_payment,
    send_notification,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("booking_service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    logger.info("Booking Service database tables are ready")
    yield


app = FastAPI(
    title="Bus Booking - Booking Service",
    description="Coordinates bus bookings across microservices.",
    version="1.0.0",
    lifespan=lifespan,
)


def error_response(code: str, message: str, status_code: int):
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
            }
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return error_response(
        code=f"HTTP_{exc.status_code}",
        message=str(exc.detail),
        status_code=exc.status_code,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    return error_response(
        code="VALIDATION_ERROR",
        message="Request validation failed",
        status_code=422,
    )


@app.exception_handler(Exception)
async def unexpected_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error while processing request")
    return error_response(
        code="INTERNAL_SERVER_ERROR",
        message="Internal server error",
        status_code=500,
    )



@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.get("/health")
def health():
    return {"status": "healthy", "service": "booking-service"}


def save_failure(
    db: Session,
    record: IdempotencyRecord,
    status_code: int,
    detail: str,
):
    record.status = "FAILED"
    record.response_json = json.dumps({
        "http_status": status_code,
        "detail": detail,
    })
    db.commit()


@app.post(
    "/api/v1/bookings",
    response_model=BookingResponse,
    status_code=201,
)
def create_booking(
    data: BookingCreate,
    request: Request,
    idempotency_key: str = Header(
        ...,
        alias="Idempotency-Key",
        min_length=1,
        max_length=255,
    ),
    db: Session = Depends(get_db),
):
    request_id = request.state.request_id
    canonical_request = json.dumps(
        data.model_dump(),
        sort_keys=True,
        separators=(",", ":"),
    )
    fingerprint = hashlib.sha256(
        canonical_request.encode("utf-8")
    ).hexdigest()

    record = IdempotencyRecord(
        idempotency_key=idempotency_key,
        request_fingerprint=fingerprint,
        status="PROCESSING",
    )
    db.add(record)

    try:
        db.commit()
        db.refresh(record)
    
    except IntegrityError:
        db.rollback()

        deadline = time.monotonic() + 30

        while True:
            existing = db.scalar(
                select(IdempotencyRecord).where(
                    IdempotencyRecord.idempotency_key == idempotency_key
                )
            )

            if existing is None:
                raise HTTPException(
                    status_code=503,
                    detail="Could not verify the previous request",
                )

            if existing.request_fingerprint != fingerprint:
                raise HTTPException(
                    status_code=409,
                    detail="Idempotency-Key was already used with a different request",
                )

            if existing.status == "COMPLETED" and existing.response_json:
                logger.info(
                    "Idempotency replay: key=%s",
                    idempotency_key,
                )
                return json.loads(existing.response_json)

            if existing.status == "FAILED" and existing.response_json:
                saved_error = json.loads(existing.response_json)
                raise HTTPException(
                    status_code=saved_error["http_status"],
                    detail=saved_error["detail"],
                )

            if time.monotonic() >= deadline:
                raise HTTPException(
                    status_code=409,
                    detail="Request with this Idempotency-Key is still processing; retry shortly",
                )

            time.sleep(0.1)
            db.expire_all()

    try:
        seat = reserve_seat(data.trip_id, request_id)
    except ValueError as exc:
        db.rollback()
        save_failure(db, record, 409, str(exc))
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except RuntimeError as exc:
        db.rollback()
        save_failure(
            db, record, 503,
            "Seat Service is currently unavailable",
        )
        raise HTTPException(
            status_code=503,
            detail="Seat Service is currently unavailable",
        ) from exc

    booking = Booking(
        trip_id=data.trip_id,
        seat_reservation_id=seat["id"],
        status="PENDING",
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)

    try:
        payment = process_payment(
            booking_id=booking.id,
            amount=data.amount,
            request_id=request_id,
        )
        booking.payment_id = payment["id"]
        booking.status = "CONFIRMED"
        db.commit()
        db.refresh(booking)

        send_notification(
            booking_id=booking.id,
            recipient=data.recipient,
            message=(
                f"Your booking {booking.id} for trip "
                f"{booking.trip_id} is confirmed."
            ),
            request_id=request_id,
        )

    except ValueError as exc:
        db.rollback()
        save_failure(db, record, 409, str(exc))
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except RuntimeError as exc:
        db.rollback()
        save_failure(
            db, record, 503,
            "A downstream service is currently unavailable",
        )
        raise HTTPException(
            status_code=503,
            detail="A downstream service is currently unavailable",
        ) from exc

    result = {
        "id": booking.id,
        "trip_id": booking.trip_id,
        "seat_reservation_id": booking.seat_reservation_id,
        "payment_id": booking.payment_id,
        "status": booking.status,
    }

    record.status = "COMPLETED"
    record.response_json = json.dumps(result)
    db.commit()

    logger.info(
        "Booking workflow completed: booking_id=%s request_id=%s",
        booking.id,
        request_id,
    )
    return result
