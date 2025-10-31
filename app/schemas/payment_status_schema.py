# app/schemas/payment_status.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from enum import Enum


class PaymentStatusEnum(str, Enum):
    """Enum for payment status values"""
    PENDING = "pending"
    PAID = "paid"
    PARTIALLY_PAID = "partially_paid"
    REFUNDED = "refunded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PaymentStatusResponse(BaseModel):
    """Response model for Payment Status"""
    id: int
    status: PaymentStatusEnum
    total_payment: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaymentStatusBase(BaseModel):
    """Base model for creating/updating Payment Status"""
    status: PaymentStatusEnum = Field(
        ...,
        alias="status",
        description="Current payment status.",
        example=PaymentStatusEnum.PENDING
    )
    total_payment: int = Field(
        ...,
        alias="totalPayment",
        description="Total payment amount in smallest currency unit (e.g., cents/paise). Must be non-negative.",
        example=50000
    )

    # Validators
    @field_validator("total_payment")
    def validate_total_payment(cls, v):
        if v < 0:
            raise ValueError("Total payment cannot be negative.")
        if v > 999999999999:  # Max value for reasonable payment (999 billion)
            raise ValueError("Total payment exceeds maximum allowed value.")
        return v

    class Config:
        populate_by_name = True
        use_enum_values = True


class PaymentStatusCreate(PaymentStatusBase):
    """Model for creating a new Payment Status record"""
    pass


class PaymentStatusUpdate(BaseModel):
    """Model for updating an existing Payment Status (all fields optional)"""
    status: Optional[PaymentStatusEnum] = Field(
        None,
        alias="status",
        description="Current payment status.",
        example=PaymentStatusEnum.PAID
    )
    total_payment: Optional[int] = Field(
        None,
        alias="totalPayment",
        description="Total payment amount.",
        example=75000
    )

    # Reuse validator from base class
    @field_validator("total_payment")
    def validate_total_payment(cls, v):
        if v is not None:
            if v < 0:
                raise ValueError("Total payment cannot be negative.")
            if v > 999999999999:
                raise ValueError("Total payment exceeds maximum allowed value.")
        return v

    class Config:
        populate_by_name = True
        use_enum_values = True