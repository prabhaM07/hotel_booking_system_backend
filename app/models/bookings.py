# app/models/bookings.py
from sqlalchemy import Column, Integer, DateTime, Date, func, ForeignKey, CheckConstraint, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.core.database_postgres import Base
from app.models.Enum import BookingStatusEnum, PaymentStatusEnum


class Bookings(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    user_id = Column(
        Integer,
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False
    )
    room_id = Column(
        Integer,
        ForeignKey("rooms.id", ondelete="CASCADE"),
        nullable=False
    )
    check_in = Column(Date, nullable=False)
    check_out = Column(Date, nullable=False)
    total_amount = Column(Integer, nullable=False)
    booking_status = Column(
        SQLEnum(BookingStatusEnum, name="booking_status_enum", create_type=False),
        nullable=False,
        default=BookingStatusEnum.PENDING.value
    )
    payment_status = Column(
        SQLEnum(PaymentStatusEnum, name="payment_status_enum", create_type=False),
        nullable=False,
        default=PaymentStatusEnum.PAID.value
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationships
    user = relationship(
        "User",
        back_populates="bookings",
        lazy='joined'
    )
    
    room = relationship(
        "Rooms",
        back_populates="bookings",
        lazy='joined'
    )
    
    booking_addons = relationship(
        "BookingAddon",
        back_populates="bookings",
        lazy='joined',
        cascade="all, delete-orphan"
    )
    
    booking_status_history = relationship(
        "BookingStatusHistory",
        back_populates="booking",
        lazy='joined',
        cascade="all, delete-orphan"
    )
    
    payment = relationship(
        "Payments",
        back_populates="booking",
        lazy='joined'
    )
    
    # Reschedule relationships
    reschedules = relationship(
        "Reschedule",
        back_populates="booking",
        lazy='joined',
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "user_id > 0",
            name="check_user_id_positive"
        ),
        CheckConstraint(
            "room_id > 0",
            name="check_room_id_positive"
        ),
        CheckConstraint(
            "check_out > check_in",
            name="check_checkout_after_checkin"
        ),
        CheckConstraint(
            "total_amount >= 0",
            name="check_total_amount_non_negative"
        ),
    )