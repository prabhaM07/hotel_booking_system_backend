# app/schemas/room_type_bed_type.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional


class RoomTypeBedTypeResponse(BaseModel):
    """Response model for Room Type Bed Type"""
    id: int
    room_type_id: int
    bed_type_id: int
    num_of_beds: int

    class Config:
        from_attributes = True


class RoomTypeBedTypeBase(BaseModel):
    """Base model for creating/updating Room Type Bed Type"""
    room_type_id: int = Field(
        ...,
        alias="roomTypeId",
        description="Foreign key reference to room_type_with_size table.",
        example=1
    )
    bed_type_id: int = Field(
        ...,
        alias="bedTypeId",
        description="Foreign key reference to Bed Type table.",
        example=2
    )
    num_of_beds: int = Field(
        ...,
        alias="numOfBeds",
        description="Number of beds of this type in the room (1-20).",
        example=2
    )

    # Validators
    @field_validator("room_type_id")
    def validate_room_type_id(cls, v):
        if v <= 0:
            raise ValueError("Room type ID must be a positive integer.")
        return v

    @field_validator("bed_type_id")
    def validate_bed_type_id(cls, v):
        if v <= 0:
            raise ValueError("Bed type ID must be a positive integer.")
        return v

    @field_validator("num_of_beds")
    def validate_num_of_beds(cls, v):
        if v < 1 or v > 20:
            raise ValueError("Number of beds must be between 1 and 20.")
        return v

    class Config:
        populate_by_name = True


class RoomTypeBedTypeCreate(RoomTypeBedTypeBase):
    """Model for creating a new Room Type Bed Type association"""
    pass


class RoomTypeBedTypeUpdate(BaseModel):
    """Model for updating an existing Room Type Bed Type (all fields optional)"""
    room_type_id: Optional[int] = Field(
        None,
        alias="roomTypeId",
        description="Foreign key reference to room_type_with_size table.",
        example=1
    )
    bed_type_id: Optional[int] = Field(
        None,
        alias="bedTypeId",
        description="Foreign key reference to Bed Type table.",
        example=3
    )
    num_of_beds: Optional[int] = Field(
        None,
        alias="numOfBeds",
        description="Number of beds of this type.",
        example=3
    )

    # Reuse validators from base class
    @field_validator("room_type_id")
    def validate_room_type_id(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Room type ID must be a positive integer.")
        return v

    @field_validator("bed_type_id")
    def validate_bed_type_id(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Bed type ID must be a positive integer.")
        return v

    @field_validator("num_of_beds")
    def validate_num_of_beds(cls, v):
        if v is not None and (v < 1 or v > 20):
            raise ValueError("Number of beds must be between 1 and 20.")
        return v

    class Config:
        populate_by_name = True