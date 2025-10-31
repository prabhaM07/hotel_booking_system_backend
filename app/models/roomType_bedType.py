# app/models/room_type_bed_type.py
from sqlalchemy import Column, Integer, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database_postgres import Base


class RoomTypeBedType(Base):
    __tablename__ = "room_type_bed_type"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    room_type_id = Column(
        Integer,
        ForeignKey("room_type_with_size.id", ondelete="CASCADE"),
        nullable=False
    )
    bed_type_id = Column(
        Integer,
        ForeignKey("bed_type.id", ondelete="CASCADE"),
        nullable=False  # Changed from optional to required
    )
    num_of_beds = Column(Integer, nullable=False)

    # Relationships
    room_type = relationship(
        "RoomTypeWithSize",
        back_populates="bed_types",  # Changed from "bed_type" to "bed_types"
        lazy='joined'
    )
    bed_type = relationship(
        "BedType",  # Changed from "bed_type" to "BedType" (proper class name)
        back_populates="room_types", 
        lazy='joined'
    )

    __table_args__ = (
        CheckConstraint(
            "room_type_id > 0",
            name="check_room_type_id_positive"
        ),
        CheckConstraint(
            "bed_type_id > 0",
            name="check_bed_type_id_positive"
        ),
        CheckConstraint(
            "num_of_beds >= 1 AND num_of_beds <= 20",
            name="check_num_of_beds_range"
        ),
        UniqueConstraint(
            "room_type_id",
            "bed_type_id",
            name="unique_room_bed_type_combination"
        ),
    )