# app/schemas/rooms.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from datetime import datetime
import re

class RoomsBase(BaseModel):
    """Base model for creating/updating Rooms"""
    id: Optional[int] = None

    room_type_id: int = Field(
        ...,
        alias="roomTypeId",
        description="Foreign key reference to room_type_with_size table.",
        example=1
    )
    floor_id: int = Field(
        ...,
        alias="floorId",
        description="Foreign key reference to Floor table.",
        example=3
    )
    
    room_no: int = Field(
        ...,
        alias="roomNo",
        description="Room number (1-9999, must be unique).",
        example=101
    )
    
    status: Optional[str] = None

    # Validators
    @field_validator("room_type_id")
    def validate_room_type_id(cls, v):
        if v <= 0:
            raise ValueError("Room type ID must be a positive integer.")
        return v

    @field_validator("floor_id")
    def validate_floor_id(cls, v):
        if v < 0:
            raise ValueError("Floor ID must be a positive integer.")
        return v

    
    @field_validator("room_no")
    def validate_room_no(cls, v):
        if v < 1 or v > 9999:
            raise ValueError("Room number must be between 1 and 9999.")
        return v

    class Config:
        populate_by_name = True


class RoomTypeResponse(BaseModel):
    id: int
    room_name: str
    base_price: int
    no_of_adult: int
    no_of_child: int

    model_config = {"from_attributes": True}


