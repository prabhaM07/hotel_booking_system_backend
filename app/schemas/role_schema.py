from pydantic import BaseModel
from datetime import datetime
from sqlalchemy import Integer
from typing import Optional

class RoleSchema(BaseModel):
    id: Integer = None
    role_name: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True
