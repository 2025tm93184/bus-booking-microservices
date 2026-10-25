
import pytest
from pydantic import ValidationError

from app.schemas import BookingCreate


def test_valid_booking_data():
    booking = BookingCreate(
        trip_id=1,
        amount=50000,
        recipient="test@example.com",
    )

    assert booking.trip_id == 1
    assert booking.amount == 50000
    assert booking.recipient == "test@example.com"


def test_trip_id_must_be_positive():
    with pytest.raises(ValidationError):
        BookingCreate(
            trip_id=0,
            amount=50000,
            recipient="test@example.com",
        )


def test_amount_must_be_positive():
    with pytest.raises(ValidationError):
        BookingCreate(
            trip_id=1,
            amount=-100,
            recipient="test@example.com",
        )


def test_recipient_cannot_be_empty():
    with pytest.raises(ValidationError):
        BookingCreate(
            trip_id=1,
            amount=50000,
            recipient="",
        )
