
from pydantic import BaseModel, Field


class BookingCreate(BaseModel):
    trip_id: int = Field(gt=0)
    amount: int = Field(gt=0, le=100000000)
    recipient: str = Field(
        min_length=1,
        max_length=255,
    )


class BookingResponse(BaseModel):
    id: int
    trip_id: int
    seat_reservation_id: int
    payment_id: int | None
    status: str

    model_config = {"from_attributes": True}
