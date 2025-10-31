# app/schemas/bookings.py
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional
from datetime import datetime, date
from enum import Enum



class BookingsResponse(BaseModel):
    """Response model for Bookings"""
    id: int
    user_id: int
    room_id: int
    refund_id: Optional[int]
    payment_status_id: int
    no_of_child: int
    no_of_adult: int
    check_in: date
    check_out: date
    total_amount: int
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BookingsBase(BaseModel):
    """Base model for creating/updating Bookings"""
    user_id: int = Field(
        ...,
        alias="userId",
        description="Foreign key reference to User table.",
        example=1
    )
    room_id: int = Field(
        ...,
        alias="roomId",
        description="Foreign key reference to Rooms table.",
        example=101
    )
    refund_id: Optional[int] = Field(
        None,
        alias="refundId",
        description="Foreign key reference to Refund table (nullable).",
        example=None
    )
    payment_status_id: int = Field(
        ...,
        alias="paymentStatusId",
        description="Foreign key reference to Payment_Status table.",
        example=1
    )
    no_of_child: int = Field(
        ...,
        alias="noOfChild",
        description="Number of children (0-10).",
        example=2
    )
    no_of_adult: int = Field(
        ...,
        alias="noOfAdult",
        description="Number of adults (1-10).",
        example=2
    )
    check_in: date = Field(
        ...,
        alias="checkIn",
        description="Check-in date (must be today or future date).",
        example="2025-11-01"
    )
    check_out: date = Field(
        ...,
        alias="checkOut",
        description="Check-out date (must be after check-in date).",
        example="2025-11-05"
    )
    total_amount: int = Field(
        ...,
        alias="totalAmount",
        description="Total booking amount in smallest currency unit (must be positive).",
        example=50000
    )
    

    # Field Validators
    @field_validator("user_id")
    def validate_user_id(cls, v):
        if v <= 0:
            raise ValueError("User ID must be a positive integer.")
        return v

    @field_validator("room_id")
    def validate_room_id(cls, v):
        if v <= 0:
            raise ValueError("Room ID must be a positive integer.")
        return v

    @field_validator("refund_id")
    def validate_refund_id(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Refund ID must be a positive integer.")
        return v

    @field_validator("payment_status_id")
    def validate_payment_status_id(cls, v):
        if v <= 0:
            raise ValueError("Payment Status ID must be a positive integer.")
        return v

    @field_validator("no_of_child")
    def validate_no_of_child(cls, v):
        if v < 0 or v > 10:
            raise ValueError("Number of children must be between 0 and 10.")
        return v

    @field_validator("no_of_adult")
    def validate_no_of_adult(cls, v):
        if v < 1 or v > 10:
            raise ValueError("Number of adults must be between 1 and 10.")
        return v

    @field_validator("check_in")
    def validate_check_in(cls, v):
        today = date.today()
        if v < today:
            raise ValueError("Check-in date cannot be in the past.")
        return v

    @field_validator("total_amount")
    def validate_total_amount(cls, v):
        if v <= 0:
            raise ValueError("Total amount must be a positive integer.")
        if v > 999999999999:
            raise ValueError("Total amount exceeds maximum allowed value.")
        return v

    # Model Validator (validates multiple fields together)
    @model_validator(mode='after')
    def validate_dates(self):
        if self.check_out <= self.check_in:
            raise ValueError("Check-out date must be after check-in date.")
        
        # Optional: Validate maximum stay duration (e.g., 90 days)
        stay_duration = (self.check_out - self.check_in).days
        if stay_duration > 90:
            raise ValueError("Maximum stay duration is 90 days.")
        
        return self

    class Config:
        populate_by_name = True
        use_enum_values = True
