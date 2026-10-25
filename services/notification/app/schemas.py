
from pydantic import BaseModel, Field


class NotificationCreate(BaseModel):
    booking_id: int = Field(gt=0)
    recipient: str = Field(min_length=1, max_length=255)
    message: str = Field(min_length=1, max_length=2000)


class NotificationResponse(BaseModel):
    id: int
    booking_id: int
    recipient: str
    message: str
    status: str

    model_config = {"from_attributes": True}
