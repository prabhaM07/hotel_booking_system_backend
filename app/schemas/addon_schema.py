# app/schemas/addon.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
import re

class AddonResponse(BaseModel):
    """Response model for Addon"""
    id: int
    addon_name: str
    price: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class AddonBase(BaseModel):
    """Base model for creating/updating Addon"""
    addon_name: str = Field(
        ...,
        alias="addonName",
        description="Name of the addon (2-100 characters).",
        example="Airport Pickup"
    )
    price: int = Field(
        ...,
        alias="price",
        description="Price of the addon in smallest currency unit (must be non-negative).",
        example=2000
    )

    # Validators
    @field_validator("addon_name")
    def validate_addon_name(cls, v):
        v = v.strip()
        if not (2 <= len(v) <= 100):
            raise ValueError("Addon name must be between 2 and 100 characters long.")
        if not re.fullmatch(r"[A-Za-z0-9\s\-&,.()]+", v):
            raise ValueError("Addon name can only contain letters, numbers, spaces, and basic punctuation (-, &, comma, period, parentheses).")
        return v

    @field_validator("price")
    def validate_price(cls, v):
        if v < 0:
            raise ValueError("Price cannot be negative.")
        if v > 999999999999:
            raise ValueError("Price exceeds maximum allowed value.")
        return v

    class Config:
        populate_by_name = True


class AddonCreate(AddonBase):
    """Model for creating a new Addon"""
    pass


class AddonUpdate(BaseModel):
    """Model for updating an existing Addon (all fields optional)"""
    addon_name: Optional[str] = Field(
        None,
        alias="addonName",
        description="Name of the addon.",
        example="Spa Package"
    )
    price: Optional[int] = Field(
        None,
        alias="price",
        description="Price of the addon.",
        example=5000
    )

    # Reuse validators from base class
    @field_validator("addon_name")
    def validate_addon_name(cls, v):
        if v is not None:
            v = v.strip()
            if not (2 <= len(v) <= 100):
                raise ValueError("Addon name must be between 2 and 100 characters long.")
            if not re.fullmatch(r"[A-Za-z0-9\s\-&,.()]+", v):
                raise ValueError("Addon name can only contain letters, numbers, spaces, and basic punctuation.")
        return v

    @field_validator("price")
    def validate_price(cls, v):
        if v is not None:
            if v < 0:
                raise ValueError("Price cannot be negative.")
            if v > 999999999999:
                raise ValueError("Price exceeds maximum allowed value.")
        return v

    class Config:
        populate_by_name = True