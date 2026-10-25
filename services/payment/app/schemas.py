
from pydantic import BaseModel, Field


class PaymentCreate(BaseModel):
    booking_id: int = Field(gt=0)
    amount: int = Field(gt=0, le=100000000)


class PaymentResponse(BaseModel):
    id: int
    booking_id: int
    amount: int
    status: str

    model_config = {"from_attributes": True}
