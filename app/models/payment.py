# app/models/payment_status_history.py
from sqlalchemy import CheckConstraint, Column, Integer, DateTime, String, func, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.core.database_postgres import Base
from app.models.Enum import PaymentStatusEnum


class Payments(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    
    booking_id = Column(
        Integer,
        ForeignKey("bookings.id", ondelete="CASCADE"),  # Match the exact table name
        nullable=False
    )
    
    total_amount =  Column(
        Integer,
        nullable=False
    )
    status = Column(
        SQLEnum(PaymentStatusEnum, name="payment_status_enum", create_type=True),
        nullable=False,
        default="available"
    )
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship
    payment_status_history = relationship(
        "PaymentStatusHistory",
        back_populates="payment",
        lazy='joined'
    )
    
    booking = relationship(
        "Bookings",
        back_populates="payment",
        lazy='joined'
    )
    
    refund = relationship(
        "Refunds",
        back_populates="payment",  
        lazy='joined'
    )
    

    __table_args__ = (
        CheckConstraint(
            "booking_id > 0",
            name="check_booking_id_positive"
        ),
    )
    
 