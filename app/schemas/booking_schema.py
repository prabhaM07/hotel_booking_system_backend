from datetime import date
from pydantic import BaseModel, Field, field_validator
from app.models.Enum import BookingStatusEnum

class BookingBase(BaseModel):
    user_id: int = Field(..., gt=0, description="Foreign key to User table")
    room_id: int = Field(..., gt=0, description="Foreign key to Room table")
    check_in: date = Field(..., description="Check-in date")
    check_out: date = Field(..., description="Check-out date (must be after check-in)")
    booking_status: BookingStatusEnum = Field(default=BookingStatusEnum.CONFIRMED.value)

    model_config = {
        "from_attributes": True,  # replaces orm_mode in Pydantic v2
    }

    @field_validator("check_out")
    @classmethod
    def validate_dates(cls, v, values):
        check_in = values.data.get("check_in")
        if check_in and v <= check_in:
            raise ValueError("check_out date must be after check_in date")
        return v
