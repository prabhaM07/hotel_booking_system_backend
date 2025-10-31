# app/schemas/reschedule.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime


class RescheduleResponse(BaseModel):
    """Response model for Reschedule"""
    id: int
    booking_id: int
    new_booking_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class RescheduleBase(BaseModel):
    """Base model for creating/updating Reschedule"""
    booking_id: int = Field(
        ...,
        alias="bookingId",
        description="Foreign key reference to original Booking (old booking).",
        example=1
    )
    new_booking_id: int = Field(
        ...,
        alias="newBookingId",
        description="Foreign key reference to new Booking (rescheduled booking).",
        example=2
    )

    # Validators
    @field_validator("booking_id")
    def validate_booking_id(cls, v):
        if v <= 0:
            raise ValueError("Booking ID must be a positive integer.")
        return v

    @field_validator("new_booking_id")
    def validate_new_booking_id(cls, v):
        if v <= 0:
            raise ValueError("New Booking ID must be a positive integer.")
        return v

    class Config:
        populate_by_name = True


class RescheduleCreate(RescheduleBase):
    """Model for creating a new Reschedule record"""
    
    @field_validator("new_booking_id")
    def validate_different_bookings(cls, v, info):
        # Ensure the new booking is different from the original
        if 'booking_id' in info.data and v == info.data['booking_id']:
            raise ValueError("New booking ID must be different from the original booking ID.")
        return v


class RescheduleUpdate(BaseModel):
    """Model for updating an existing Reschedule (all fields optional)"""
    booking_id: Optional[int] = Field(
        None,
        alias="bookingId",
        description="Foreign key reference to original Booking.",
        example=3
    )
    new_booking_id: Optional[int] = Field(
        None,
        alias="newBookingId",
        description="Foreign key reference to new Booking.",
        example=4
    )

    # Reuse validators from base class
    @field_validator("booking_id")
    def validate_booking_id(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Booking ID must be a positive integer.")
        return v

    @field_validator("new_booking_id")
    def validate_new_booking_id(cls, v):
        if v is not None and v <= 0:
            raise ValueError("New Booking ID must be a positive integer.")
        return v

    class Config:
        populate_by_name = True