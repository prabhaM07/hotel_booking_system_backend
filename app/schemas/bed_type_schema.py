from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional
import re


class BedTypeSchema(BaseModel):
    id: Optional[int] = Field(None, description="Primary key (auto-generated)")
    bed_type_name: str = Field(
        ..., 
        min_length=2, 
        max_length=50, 
        description="Type of bed, e.g. Single, Double, King, Queen"
    )
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

    # --- Field Validators ---
    @field_validator("bed_type_name")
    @classmethod
    def validate_bed_type_name(cls, v: str) -> str:
        """
        Validate that bed_type_name contains only alphabetic characters and spaces,
        and is between 2 and 50 characters.
        """
        if not re.match(r"^[A-Za-z\s]+$", v.strip()):
            raise ValueError("Bed type name must contain only letters and spaces.")
        return v.strip().title()

    class Config:
        from_attributes = True  
        arbitrary_types_allowed = True  
