
import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.models import Payment
from app.schemas import PaymentCreate, PaymentResponse


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("payment_service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    logger.info("Payment Service database tables are ready")
    yield


app = FastAPI(
    title="Bus Booking - Payment Service",
    description="Simulates payment processing for bus bookings.",
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
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "payment-service",
    }


@app.post(
    "/api/v1/payments",
    response_model=PaymentResponse,
    status_code=201,
)
def create_payment(
    data: PaymentCreate,
    db: Session = Depends(get_db),
):
    existing = db.scalar(
        select(Payment).where(Payment.booking_id == data.booking_id)
    )
    if existing:
        if existing.amount != data.amount:
            raise HTTPException(
                status_code=409,
                detail="A payment already exists for this booking with a different amount",
            )
        return existing

    payment = Payment(
        booking_id=data.booking_id,
        amount=data.amount,
        status="SUCCESS",
    )
    db.add(payment)

    try:
        db.commit()
        db.refresh(payment)
    except IntegrityError:
        db.rollback()
        existing = db.scalar(
            select(Payment).where(Payment.booking_id == data.booking_id)
        )
        if existing and existing.amount == data.amount:
            return existing
        raise HTTPException(
            status_code=409,
            detail="Payment already exists for this booking",
        )

    logger.info(
        "Mock payment processed: payment_id=%s booking_id=%s",
        payment.id,
        payment.booking_id,
    )
    return payment
