# app/models/features.py
from sqlalchemy import Column, String, DateTime, LargeBinary, func, Integer
from app.core.database_postgres import Base
from sqlalchemy.orm import relationship
from app.models.associations import room_type_features


class Features(Base):
    __tablename__ = "features"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    feature_name = Column(String(100), nullable=False, unique=True)
    image = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    room_type = relationship(
        "RoomTypeWithSizes",
        secondary=room_type_features,
        back_populates="feature",
        lazy="joined"
    )
   