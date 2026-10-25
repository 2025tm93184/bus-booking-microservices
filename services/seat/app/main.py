
import logging
import os
import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.models import Reservation, Trip
from app.schemas import TripCreate, TripResponse, ReservationResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seat_service")

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






@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    logger.info("Seat Service database tables are ready")
    yield


app = FastAPI(
    title="Bus Booking - Seat Service",
    description="Manages bus trips, seat capacity and reservations.",
    version="1.0.0",
    lifespan=lifespan,
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

    logger.info(
        '{"event":"request_started","request_id":"%s","method":"%s","path":"%s"}',
        request_id,
        request.method,
        request.url.path,
    )

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.get("/health")
def health():
    return {"status": "healthy", "service": "seat-service"}


@app.post(
    "/api/v1/trips",
    response_model=TripResponse,
    status_code=201,
)
def create_trip(data: TripCreate, db: Session = Depends(get_db)):
    trip = Trip(name=data.name.strip(), total_seats=data.total_seats)

    if not trip.name:
        raise HTTPException(status_code=422, detail="Trip name cannot be blank")

    db.add(trip)
    db.commit()
    db.refresh(trip)
    return trip


@app.get("/api/v1/trips", response_model=list[TripResponse])
def list_trips(db: Session = Depends(get_db)):
    return db.scalars(select(Trip).order_by(Trip.id)).all()


@app.get("/api/v1/trips/{trip_id}/availability")
def get_availability(trip_id: int, db: Session = Depends(get_db)):
    trip = db.get(Trip, trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")

    reserved_count = db.scalar(
        select(func.count())
        .select_from(Reservation)
        .where(
            Reservation.trip_id == trip_id,
            Reservation.status == "RESERVED",
        )
    )

    return {
        "trip_id": trip.id,
        "total_seats": trip.total_seats,
        "reserved_seats": reserved_count,
        "available_seats": trip.total_seats - reserved_count,
    }


@app.post(
    "/api/v1/trips/{trip_id}/reservations",
    response_model=ReservationResponse,
    status_code=201,
)
def reserve_seat(trip_id: int, db: Session = Depends(get_db)):
    try:
        # Lock the trip row so concurrent reservations for this trip
        # are processed one at a time.
        trip = db.scalar(
            select(Trip)
            .where(Trip.id == trip_id)
            .with_for_update()
        )

        if trip is None:
            raise HTTPException(status_code=404, detail="Trip not found")

        reserved_numbers = set(
            db.scalars(
                select(Reservation.seat_number).where(
                    Reservation.trip_id == trip_id,
                    Reservation.status == "RESERVED",
                )
            ).all()
        )

        seat_number = next(
            (
                number
                for number in range(1, trip.total_seats + 1)
                if number not in reserved_numbers
            ),
            None,
        )

        if seat_number is None:
            raise HTTPException(
                status_code=409,
                detail="No seats available for this trip",
            )

        reservation = Reservation(
            trip_id=trip_id,
            seat_number=seat_number,
            status="RESERVED",
        )
        db.add(reservation)
        db.commit()
        db.refresh(reservation)

        logger.info(
            '{"event":"seat_reserved","trip_id":%s,"seat_number":%s}',
            trip_id,
            seat_number,
        )
        return reservation

    except HTTPException:
        db.rollback()
        raise
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Seat reservation conflict; please retry",
        )
    except Exception:
        db.rollback()
        logger.exception("Unexpected error while reserving a seat")
        raise HTTPException(
            status_code=500,
            detail="Internal server error",
        )


@app.get("/api/v1/reservations", response_model=list[ReservationResponse])
def list_reservations(db: Session = Depends(get_db)):
    return db.scalars(
        select(Reservation).order_by(Reservation.id)
    ).all()
