# app/models/profile.py
from sqlalchemy import (
    Column,
    DateTime,
    LargeBinary,
    ForeignKey,
    String,
    Date,
    func,
    CheckConstraint,
    Integer
)
from app.core.database_postgres import Base
from sqlalchemy.orm import relationship
from sqlalchemy_utils import CompositeType


class Profiles(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    dob = Column(Date, nullable=True)
    
    # Composite type for address
    address = Column(
        CompositeType(
            "address_type",
            [
                Column("street", String, nullable=True),
                Column("city", String, nullable=True),
                Column("state", String, nullable=True),
                Column("country", String, nullable=True),
                Column("pincode", String, nullable=True),
            ],
        ),
        nullable=True
    )
    
    image_url = Column(String, nullable=True) 
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now(), nullable=False)

    user = relationship("Users", back_populates="profile", uselist=False)

    __table_args__ = (
        CheckConstraint("char_length((address).city) <= 50", name="check_city_length"),
        CheckConstraint("char_length((address).state) <= 50", name="check_state_length"),
        CheckConstraint("char_length((address).country) <= 50", name="check_country_length"),
        CheckConstraint("((address).pincode ~ '^[0-9]{5,6}$') OR (address).pincode IS NULL", name="check_valid_pincode"),
    )