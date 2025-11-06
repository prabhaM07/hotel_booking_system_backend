# app/models/room_type_bed_type.py
from sqlalchemy import Column, Integer, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database_postgres import Base


class RoomTypeBedTypes(Base):
    __tablename__ = "room_type_bed_types"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    room_type_id = Column(
        Integer,
        ForeignKey("room_type_with_sizes.id", ondelete="CASCADE"),
        nullable=False
    )
    bed_type_id = Column(
        Integer,
        ForeignKey("bed_types.id", ondelete="CASCADE"),
        nullable=False  
    )
    num_of_beds = Column(Integer, nullable=False)

    room_type = relationship(
        "RoomTypeWithSizes",
        back_populates="bed_type", 
        lazy='joined'
    )
    bed_type = relationship(
        "BedTypes",  
        back_populates="room_type", 
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