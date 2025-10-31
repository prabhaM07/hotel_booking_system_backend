# app/schemas/floor.py
from pydantic import BaseModel, Field, field_validator



class FloorBase(BaseModel):
    """Base model for creating/updating Floor"""
    floor_no: int = Field(
        ...,
        alias="floorNo",
        description="Floor number (-5 to 100, where negative numbers represent basement levels).",
        example=3
    )

    # Validators
    @field_validator("floor_no")
    def validate_floor_no(cls, v):
        if v < -5 or v > 100:
            raise ValueError("Floor number must be between -5 (basement) and 100.")
        return v

    class Config:
        populate_by_name = True

