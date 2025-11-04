from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Literal
import re


class UserResponse(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone_no: str
    role: Literal["user", "admin"] 
    

from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Literal
import re

class UserBase(BaseModel):
    first_name: str = Field(
        ...,
        alias="firstName",
        description="User's first name (only alphabetic, 1–50 chars).",
        example="John"
    )
    last_name: str = Field(
        ...,
        alias="lastName",
        description="User's last name (only alphabetic, 1–50 chars).",
        example="Doe"
    )
    email: EmailStr = Field(
        ...,
        alias="email",
        description="Valid email address of the user.",
        example="john.doe@example.com"
    )
    
    role: Literal["user", "admin"] = Field(
        default="user",
        description="Role of the user. Can be either 'user' or 'admin'.",
        example="user"
    )
    
    password: str = Field(
        ...,
        alias="password",
        description="Password with at least 6 chars, one uppercase, one number, one special symbol.",
        example="John@123"
    )
    
    phone_no: str = Field(
        ...,
        alias="phoneNo",
        description="10-digit mobile number (should not start with 0).",
        example="9876543210"
    )

    # Validators
    @field_validator("first_name", "last_name")
    def validate_name(cls, v):
        v = v.strip()
        if not (1 <= len(v) <= 50):
            raise ValueError("Name must be between 1 and 50 characters long.")
        if not re.fullmatch(r"[A-Za-z]+", v):
            raise ValueError("Name must contain only alphabetic characters.")
        return v

    @field_validator("phone_no")
    def validate_phone(cls, v):
        v = v.strip()
        if not re.fullmatch(r"^[1-9][0-9]{9}$", v):
            raise ValueError("Enter a valid 10-digit phone number (should not start with 0).")
        return v

    @field_validator("password")
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters long.")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one number.")
        if not re.search(r"[!@#$%^&*()_+\-=\[\]{}|;:,.<>/?~]", v):
            raise ValueError("Password must contain at least one special character.")
        return v
    
    model_config = {
        "from_attributes": True
    }



class UserForgetPassword(BaseModel):
    email: EmailStr = Field(
        ...,
        alias="email",
        description="Registered email address.",
        example="john.doe@example.com"
    )
    prev_password: str = Field(
        ...,
        alias="prevPassword",
        description="Previous password (for verification).",
        example="John@123"
    )
    cur_password: str = Field(
        ...,
        alias="curPassword",
        description="New password (must differ from previous).",
        example="John@456"
    )

