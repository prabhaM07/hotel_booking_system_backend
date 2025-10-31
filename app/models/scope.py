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
from app.models.associations import role_scope

class Scopes(Base):
    __tablename__ = "scope"
    
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    scope_name = Column(String(100), nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    update_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    
    # Relationship to Role
    
    role = relationship(
        "Role",
        secondary=role_scope,
        back_populates="scope",
        lazy="joined"
    )