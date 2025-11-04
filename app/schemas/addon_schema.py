from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class AddonSchema(BaseModel):
    id: Optional[int] = None
    addon_name: str = Field(..., min_length=2, max_length=100)
    base_price: int = Field(..., gt=0, le=100000)
    image: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True
