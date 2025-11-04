# app/models/booking_status_history.py
from wsgiref import validate
from sqlalchemy import Column, Integer, DateTime, String, func, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from app.core.database_postgres import Base

class RefundStatusHistory(Base):
    __tablename__ = "refund_status_history"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    refund_id = Column(
        Integer,
        ForeignKey("refunds.id", ondelete="CASCADE"),
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

    refund = relationship(
        "Refunds",
        back_populates="refund_status_history",  
        lazy='joined'
    )
    
    __table_args__ = (
        CheckConstraint(
            "refund_id > 0",
            name="check_booking_id_positive"
        ),
    )
  