# app/models/addon.py
from sqlalchemy import Column, Integer, String, DateTime, func, CheckConstraint
from sqlalchemy.orm import relationship
from app.core.database_postgres import Base


class Addon(Base):
    __tablename__ = "Addon"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    addon_name = Column(String(100), nullable=False, unique=True)
    price = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationship with BookingAddon
    booking_addons = relationship(
        "BookingAddon",
        back_populates="addon",
        lazy='select'
    )

    __table_args__ = (
        CheckConstraint(
            "char_length(addon_name) >= 2 AND char_length(addon_name) <= 100",
            name="check_addon_name_length"
        ),
        CheckConstraint(
            "price > 0 AND price <= 100000",
            name="check_price_range"
        ),
    )