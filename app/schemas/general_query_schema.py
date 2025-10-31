from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from typing import Optional

class UserQuerySchema(BaseModel):
    id: Optional[str] = Field(None, description="Primary key (auto-generated)")
    email: EmailStr = Field(..., description="Valid email address of the user")
    phone_no: int = Field(..., ge=1000000000, le=999999999999, description="Phone number (10–12 digits)")
    subject: str = Field(..., min_length=3, max_length=100, description="Subject of the query")
    description: str = Field(..., min_length=5, max_length=500, description="Detailed description of the query")
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow, description="Timestamp when record was created")
    response: Optional[str] = Field(None, max_length=500, description="Response from admin/support")
    response_at: Optional[datetime] = Field(None, description="Timestamp when the response was made")

    # Validators
    @field_validator("phone_no")
    @classmethod
    def validate_phone(cls, value: int):
        if not (10 <= len(str(value)) <= 12):
            raise ValueError("Phone number must be between 10 and 12 digits.")
        return value

    @field_validator("subject")
    @classmethod
    def validate_subject(cls, value: str):
        if value.isdigit():
            raise ValueError("Subject cannot be only numeric.")
        return value.strip()

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str):
        if len(value.strip()) < 5:
            raise ValueError("Description must contain at least 5 characters.")
        return value.strip()

    class Config:
        orm_mode = True
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "phone_no": 9876543210,
                "subject": "App login issue",
                "description": "Unable to login after recent update.",
                "created_at":None,
                "response": None,
                "response_at": None
            }
        }

class GeneralQueryResponseSchema(BaseModel):
    response: Optional[str] = Field(None, max_length=500, description="Response from admin/support")
    response_at: Optional[datetime] = Field(None, description="Timestamp when the response was made")
    