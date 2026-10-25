
import pytest
from pydantic import ValidationError

from app.schemas import PaymentCreate


def test_valid_payment_data():
    payment = PaymentCreate(booking_id=1, amount=50000)

    assert payment.booking_id == 1
    assert payment.amount == 50000


def test_booking_id_must_be_positive():
    with pytest.raises(ValidationError):
        PaymentCreate(booking_id=0, amount=50000)


def test_payment_amount_must_be_positive():
    with pytest.raises(ValidationError):
        PaymentCreate(booking_id=1, amount=0)


def test_payment_amount_cannot_exceed_limit():
    with pytest.raises(ValidationError):
        PaymentCreate(booking_id=1, amount=100000001)
