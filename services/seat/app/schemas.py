
from pydantic import BaseModel, Field


class TripCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    total_seats: int = Field(gt=0, le=1000)


class TripResponse(BaseModel):
    id: int
    name: str
    total_seats: int

    model_config = {"from_attributes": True}


class ReservationResponse(BaseModel):
    id: int
    trip_id: int
    seat_number: int
    status: str

    model_config = {"from_attributes": True}
