# app/models/floor.py
from sqlalchemy import Column, Integer, DateTime, func, CheckConstraint
from sqlalchemy.orm import relationship
from app.core.database_postgres import Base


class Floors(Base):
    __tablename__ = "floors"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    floor_no = Column(Integer, nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    room = relationship(
        "Rooms",
        back_populates="floor",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy='joined'
    )

    __table_args__ = (
        CheckConstraint(
            "floor_no >= -5 AND floor_no <= 100",
            name="check_floor_no_range"
        ),
    )