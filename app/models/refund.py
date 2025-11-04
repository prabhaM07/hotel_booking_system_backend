from sqlalchemy import CheckConstraint, Column, Integer, DateTime, String, func, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.core.database_postgres import Base
from app.models.Enum import RefundStatusEnum


class Refunds(Base):
    __tablename__ = "refunds"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    
    payment_id = Column(
        Integer,
        ForeignKey("payments.id", ondelete="CASCADE"), 
        nullable=False
    )
        
    status = Column(
        SQLEnum(RefundStatusEnum, name="refund_status_enum", create_type=True),
        nullable=False,
        default="available"
    )
    
    reason = Column(
        String[200],
        nullable=False
    )
    
    total_amount = Column(
        Integer,
        nullable=False
    )
    
    refund_amount = Column(
        Integer,
        nullable=False
    )
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


    payment = relationship(
        "Payments",
        back_populates="refund",  
        lazy='joined'
    )

    refund_status_history = relationship(
        "RefundStatusHistory",
        back_populates="refund",  
        lazy='joined'
    )
    
    __table_args__ = (
        CheckConstraint(
            "payment_id > 0",
            name="check_booking_id_positive"
        ),
    )
    
 