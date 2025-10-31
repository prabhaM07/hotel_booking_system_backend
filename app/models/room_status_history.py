# app/models/room_status_history.py
from wsgiref import validate
from sqlalchemy import Column, Integer, DateTime, String, func, ForeignKey, CheckConstraint, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.core.database_postgres import Base
from app.models.Enum import RoomStatusEnum

class RoomStatusHistory(Base):
    __tablename__ = "room_status_history"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    room_id = Column(
        Integer,
        ForeignKey("rooms.id", ondelete="CASCADE"),
        nullable=False
    )
    old_status = Column(
        String(50),
        nullable=False
    )
    new_status = Column(
        String(50),
        nullable=False
    )
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    changed_by = Column(Integer, ForeignKey("user.id"), nullable=True)
    
    room = relationship(
        "Rooms",
        back_populates="status_history", 
        lazy='joined'
    )

    user = relationship(
        "User",
        back_populates="status_history_room",  
        lazy='joined'
    )
    
    __table_args__ = (
        CheckConstraint(
            "room_id > 0",
            name="check_room_id_positive"
        ),
        
    )
    