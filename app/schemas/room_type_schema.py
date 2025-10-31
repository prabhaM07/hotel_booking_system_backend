# app/schemas/room_type.py
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime
import re

class RoomTypeResponse(BaseModel):

    """Base model for creating/updating Room Type"""
    room_name: str = Field(
        ...,
        alias="roomName",
        description="Name of the room type (2-100 chars, alphanumeric with spaces allowed).",
        example="Deluxe Suite"
    )
    
    base_price: int = Field(
        ...,
        alias="basePrice",
        description="Base price per night in currency units (must be positive).",
        example=5000
    )
    no_of_adult: int = Field(
        ...,
        alias="noOfAdult",
        description="Maximum number of adults allowed (1-10).",
        example=2
    )
    no_of_child: int = Field(
        ...,
        alias="noOfChild",
        description="Maximum number of children allowed (0-10).",
        example=2
    )

    
    # Validators
    @field_validator("room_name")
    def validate_room_name(cls, v):
        v = v.strip()
        if not (2 <= len(v) <= 100):
            raise ValueError("Room name must be between 2 and 100 characters long.")
        if not re.fullmatch(r"[A-Za-z0-9\s]+", v):
            raise ValueError("Room name must contain only alphanumeric characters and spaces.")
        return v

    
    @field_validator("base_price")
    def validate_base_price(cls, v):
        if v <= 0:
            raise ValueError("Base price must be a positive integer.")
        if v > 1000000:
            raise ValueError("Base price cannot exceed 1,000,000.")
        return v

    @field_validator("no_of_adult")
    def validate_no_of_adult(cls, v):
        if v < 1 or v > 10:
            raise ValueError("Number of adults must be between 1 and 10.")
        return v

    @field_validator("no_of_child")
    def validate_no_of_child(cls, v):
        if v < 0 or v > 10:
            raise ValueError("Number of children must be between 0 and 10.")
        return v

    class Config:
        populate_by_name = True



