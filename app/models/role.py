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

class Roles(Base):
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    role_name = Column(String(50), nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    update_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationship to User
    user = relationship(
        "Users",
        back_populates="role",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    
    scope = relationship(
        "Scopes",
        secondary=role_scopes,
        back_populates="role",
        lazy="joined"
    )