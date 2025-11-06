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

