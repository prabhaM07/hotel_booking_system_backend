from sqlalchemy import Column, String, DateTime, func,Integer
from app.core.database_postgres import Base
from sqlalchemy.orm import relationship

class BedType(Base):
    __tablename__ = "bed_type"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    bed_type_name = Column(String(50), nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    room_types = relationship(
        "RoomTypeBedType",
        back_populates="bed_type",
        lazy='joined'
    )
    
    
