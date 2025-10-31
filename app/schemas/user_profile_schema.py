from pydantic import BaseModel
from datetime import datetime,date
from typing import Optional

class Address(BaseModel):
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    pincode: Optional[str] = None

class UserProfileBase(BaseModel):
    address: Optional[Address] = None
    DOB: Optional[date] = None
    updated_at: Optional[datetime] = None
