from pydantic import BaseModel, Field, field_validator
from app.models.Enum import PaymentStatusEnum

class PaymentBase(BaseModel):
    booking_id: int = Field(..., gt=0)
    total_amount: int = Field(..., gt=0)
    status: PaymentStatusEnum

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        # Automatically accept either Enum or string values
        if isinstance(v, PaymentStatusEnum):
            return v
        try:
            return PaymentStatusEnum(v)
        except ValueError:
            raise ValueError(f"Invalid payment status: {v}")
