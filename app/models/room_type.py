# app/models/room_type.py
from sqlalchemy import Column, Integer, String, DateTime, Text, func, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.core.database_postgres import Base
from app.models.associations import room_type_features


class RoomTypeWithSizes(Base):
    __tablename__ = "room_type_with_sizes"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    room_name = Column(String(100), nullable=False, unique=True)
    images = Column(JSONB, nullable=False,default = list)
    base_price = Column(Integer, nullable=False)
    no_of_adult = Column(Integer, nullable=False)
    no_of_child = Column(Integer, nullable=False)
    search_text = Column(Text) 
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    room = relationship(
        "Rooms",
        back_populates="room_type",
        lazy='joined'
    )
    
    bed_type = relationship(
        "RoomTypeBedTypes",
        back_populates="room_type",
        lazy='joined'
    )
    
    feature = relationship(
        "Features",
        secondary=room_type_features,
        back_populates="room_type",
        lazy="joined"
    )
    
    
    __table_args__ = (
        CheckConstraint(
            "char_length(room_name) >= 2 AND char_length(room_name) <= 100",
            name="check_room_name_length"
        ),
        CheckConstraint(
            "room_name ~ '^[A-Za-z0-9\\s]+$'",
            name="check_room_name_format"
        ),
        CheckConstraint(
            "base_price > 0 AND base_price <= 1000000",
            name="check_base_price_range"
        ),
        CheckConstraint(
            "no_of_adult >= 1 AND no_of_adult <= 10",
            name="check_no_of_adult_range"
        ),
        CheckConstraint(
            "no_of_child >= 0 AND no_of_child <= 10",
            name="check_no_of_child_range"
        ),
        CheckConstraint(
            "jsonb_typeof(images) = 'array' AND jsonb_array_length(images) > 0 AND jsonb_array_length(images) <= 20",
            name="check_images_array"
        ),
    )