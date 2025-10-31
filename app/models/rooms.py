# app/models/rooms.py
from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey, CheckConstraint, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.core.database_postgres import Base
from app.models.Enum import RoomStatusEnum


class Rooms(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    room_type_id = Column(
        Integer,
        ForeignKey("room_type_with_size.id", ondelete="CASCADE"),
        nullable=False
    )
    floor_id = Column(
        Integer,
        ForeignKey("floor.id", ondelete="CASCADE"),
        nullable=False
    )
    room_no = Column(Integer, nullable=False, unique=True)
    
    status = Column(
        SQLEnum(RoomStatusEnum, name="room_status_enum", create_type=True),
        nullable=False,
        default="available"
    )
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    room_type = relationship(
        "RoomTypeWithSize",
        back_populates="rooms",
        lazy="joined"
    )
    
    floor = relationship(
        "Floor",
        back_populates="rooms",
        lazy='joined'
    )
    
    bookings = relationship(
        "Bookings",
        back_populates="room",
        lazy='joined'
    )

    status_history = relationship(
        "RoomStatusHistory",
        back_populates="room",
        lazy='joined'
    )
    
    __table_args__ = (
        CheckConstraint(
            "room_type_id > 0",
            name="check_room_type_id_positive"
        ),
        CheckConstraint(
            "floor_id >= 0",
            name="check_floor_id_positive"
        ),
        CheckConstraint(
            "room_no >= 1 AND room_no <= 9999",
            name="check_room_no_range"
        ),
    )