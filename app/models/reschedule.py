# app/models/reschedule.py
from sqlalchemy import Column, Integer, DateTime, func, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database_postgres import Base


class Reschedule(Base):
    __tablename__ = "reschedule"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    
    booking_id = Column(
        Integer,
        ForeignKey("bookings.id", ondelete="CASCADE"),
        nullable=False
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    booking = relationship(
        "Bookings",
        back_populates="reschedules",
        lazy='joined'
    )
    

    __table_args__ = (
        CheckConstraint(
            "booking_id > 0",
            name="check_booking_id_positive"
        ),
        UniqueConstraint(
            "booking_id",
            name="unique_booking_reschedule"
        ),
    )