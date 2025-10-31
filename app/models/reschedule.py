# app/models/reschedule.py
from sqlalchemy import Column, Integer, DateTime, func, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database_postgres import Base


class Reschedule(Base):
    __tablename__ = "Reschedule"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    
    booking_id = Column(
        Integer,
        ForeignKey("bookings.id", ondelete="CASCADE"),
        nullable=False
    )
    new_booking_id = Column(
        Integer,
        ForeignKey("bookings.id", ondelete="CASCADE"),
        nullable=False
    )
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships - using back_populates
    original_booking = relationship(
        "Bookings",
        foreign_keys=[booking_id],
        back_populates="reschedules",
        lazy='joined'
    )
    
    rescheduled_booking = relationship(
        "Bookings",
        foreign_keys=[new_booking_id],
        back_populates="new_reschedules",
        lazy='joined'
    )

    __table_args__ = (
        CheckConstraint(
            "booking_id > 0",
            name="check_booking_id_positive"
        ),
        CheckConstraint(
            "new_booking_id > 0",
            name="check_new_booking_id_positive"
        ),
        CheckConstraint(
            "booking_id != new_booking_id",
            name="check_different_bookings"
        ),
        UniqueConstraint(
            "booking_id",
            name="unique_booking_reschedule"
        ),
    )