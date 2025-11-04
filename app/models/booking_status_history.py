# app/models/booking_status_history.py
from wsgiref import validate
from sqlalchemy import Column, Integer, DateTime, String, func, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from app.core.database_postgres import Base

class BookingStatusHistory(Base):
    __tablename__ = "booking_status_history"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    booking_id = Column(
        Integer,
        ForeignKey("bookings.id", ondelete="CASCADE"),
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

    booking = relationship(
        "Bookings",
        back_populates="booking_status_history",  
        lazy='joined'
    )
    
    __table_args__ = (
        CheckConstraint(
            "booking_id > 0",
            name="check_booking_id_positive"
        ),
    )
  