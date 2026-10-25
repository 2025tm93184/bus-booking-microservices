
import pytest
from pydantic import ValidationError

from app.schemas import TripCreate


def test_valid_trip_data():
    trip = TripCreate(name="Test Bus", total_seats=5)

    assert trip.name == "Test Bus"
    assert trip.total_seats == 5


def test_trip_requires_positive_capacity():
    with pytest.raises(ValidationError):
        TripCreate(name="Test Bus", total_seats=0)


def test_trip_capacity_cannot_exceed_limit():
    with pytest.raises(ValidationError):
        TripCreate(name="Test Bus", total_seats=1001)


def test_trip_name_cannot_be_empty():
    with pytest.raises(ValidationError):
        TripCreate(name="", total_seats=5)
