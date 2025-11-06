# app/models/role.py
from sqlalchemy import (
    Column,
    DateTime,
    String,
    func,
    Integer
)
from app.core.database_postgres import Base
from sqlalchemy.orm import relationship
from app.models.associations import role_scopes

class Scopes(Base):
    __tablename__ = "scopes"
    
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    scope_name = Column(String(100), nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    update_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
        
    role = relationship(
        "Roles",
        secondary=role_scopes,
        back_populates="scope",
        lazy="joined"
    )