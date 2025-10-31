from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional


class FeatureSchema(BaseModel):
    feature_name: str = Field(..., min_length=2, max_length=100, description="Name of the feature")
    created_at: Optional[datetime] = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = Field(default_factory=datetime.now)
  
    class Config:
        orm_mode = True
        from_attributes = True

