from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
from app.models.Enum import RoomStatusEnum,PaymentStatusEnum,BookingStatusEnum


class RoomStatusHistoryBase(BaseModel):
    room_id: int = Field(..., gt=0, description="Associated room ID, must be positive")
    old_status: str = Field(..., min_length=3, max_length=50, description="Previous room status")
    new_status: str = Field(..., min_length=3, max_length=50, description="New room status")
    changed_by: Optional[int] = Field(None, gt=0, description="User ID who changed the status")

    @validator("new_status", "old_status")
    def validate_status(cls, v):
        valid_values = [status.value for status in RoomStatusEnum]
        if v not in valid_values:
            raise ValueError(f"Invalid status '{v}'. Must be one of {valid_values}")
        return v


class PaymentStatusHistoryBase(BaseModel):
    payment_id: int = Field(..., gt=0, description="Associated payment ID, must be positive")
    old_status: str = Field(..., min_length=3, max_length=50, description="Previous payment status")
    new_status: str = Field(..., min_length=3, max_length=50, description="New payment status")

    @validator("new_status", "old_status")
    def validate_status(cls, v):
        valid_values = [status.value for status in PaymentStatusEnum]
        if v not in valid_values:
            raise ValueError(f"Invalid status '{v}'. Must be one of {valid_values}")
        return v



class BookingStatusHistoryBase(BaseModel):
    booking_id: int = Field(..., gt=0, description="Associated booking ID, must be positive")
    old_status: str = Field(..., min_length=3, max_length=50, description="Previous booking status")
    new_status: str = Field(..., min_length=3, max_length=50, description="New booking status")

    @validator("new_status", "old_status")
    def validate_status(cls, v):
        valid_values = [status.value for status in BookingStatusEnum]
        if v not in valid_values:
            raise ValueError(f"Invalid status '{v}'. Must be one of {valid_values}")
        return v
