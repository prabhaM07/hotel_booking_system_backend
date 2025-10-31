# app/models/payment_status_history.py
from sqlalchemy import CheckConstraint, Column, Integer, DateTime, String, func, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.core.database_postgres import Base
from app.models.Enum import PaymentStatusEnum


class PaymentStatusHistory(Base):
    __tablename__ = "Payment_Status"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    
    booking_id = Column(
        Integer,
        ForeignKey("bookings.id", ondelete="CASCADE"),  # Match the exact table name
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
    changed_by = Column(Integer, ForeignKey("user.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship
    booking = relationship(
        "Bookings",
        back_populates="payment_history",
        lazy='joined'
    )
    
    user = relationship(
        "User",
        back_populates="status_history_payment",  
        lazy='joined'
    )


    __table_args__ = (
        CheckConstraint(
            "booking_id > 0",
            name="check_booking_id_positive"
        ),
    )
    
 