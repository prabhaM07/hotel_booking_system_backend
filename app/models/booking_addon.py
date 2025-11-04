# app/models/booking_addon.py
from sqlalchemy import Column, Integer, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database_postgres import Base


class BookingAddon(Base):
    __tablename__ = "booking_addon"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    booking_id = Column(
        Integer,
        ForeignKey("bookings.id", ondelete="CASCADE"),
        nullable=False
    )
    addon_id = Column(
        Integer,
        ForeignKey("addons.id", ondelete="CASCADE"),
        nullable=False
    )
    quantity = Column(Integer, nullable=False, default=1)

    # Relationships
    bookings = relationship(
        "Bookings",
        back_populates="booking_addons",
        lazy='joined'
    )
    
    addons = relationship(
        "Addons",
        back_populates="booking_addons",
        lazy='joined'
    )

    __table_args__ = (
        CheckConstraint(
            "booking_id > 0",
            name="check_booking_id_positive"
        ),
        CheckConstraint(
            "addon_id > 0",
            name="check_addon_id_positive"
        ),
        CheckConstraint(
            "quantity >= 1 AND quantity <= 100",
            name="check_quantity_range"
        ),
        UniqueConstraint(
            "booking_id",
            "addon_id",
            name="unique_booking_addon_combination"
        ),
    )