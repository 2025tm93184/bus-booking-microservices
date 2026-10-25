
import pytest
from pydantic import ValidationError

from app.schemas import NotificationCreate


def test_valid_notification_data():
    notification = NotificationCreate(
        booking_id=1,
        recipient="test@example.com",
        message="Your booking is confirmed.",
    )

    assert notification.booking_id == 1
    assert notification.recipient == "test@example.com"
    assert notification.message == "Your booking is confirmed."


def test_booking_id_must_be_positive():
    with pytest.raises(ValidationError):
        NotificationCreate(
            booking_id=0,
            recipient="test@example.com",
            message="Booking confirmed.",
        )


def test_recipient_cannot_be_empty():
    with pytest.raises(ValidationError):
        NotificationCreate(
            booking_id=1,
            recipient="",
            message="Booking confirmed.",
        )


def test_message_cannot_be_empty():
    with pytest.raises(ValidationError):
        NotificationCreate(
            booking_id=1,
            recipient="test@example.com",
            message="",
        )
