# app/models/payment_status_history.py
from sqlalchemy import CheckConstraint, Column, Integer, DateTime, String, func, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.core.database_postgres import Base
from app.models.Enum import PaymentStatusEnum


class PaymentStatusHistory(Base):
    __tablename__ = "payment_status_history"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    
    payment_id = Column(
        Integer,
        ForeignKey("payments.id", ondelete="CASCADE"),
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

    # Relationship
    
    payment = relationship(
        "Payments",
        back_populates="payment_status_history",
        lazy='joined'
    )
   
    
 