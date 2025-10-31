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

class Role(Base):
    __tablename__ = "role"
    
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    role_name = Column(String(50), nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    update_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationship to User
    users = relationship(
        "User",
        back_populates="role",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    
     # Relationship to Role
    
    scope = relationship(
        "Scopes",
        secondary=role_scope,
        back_populates="role",
        lazy="joined"
    )