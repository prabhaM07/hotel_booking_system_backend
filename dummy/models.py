# models.py
from sqlalchemy import Column, Integer, Text, SmallInteger, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import TSVECTOR

Base = declarative_base()

class Hotel(Base):
    __tablename__ = "hotel"
    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    city = Column(Text, nullable=False)
    address = Column(Text)
    description = Column(Text)
    stars = Column(SmallInteger)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    # search_vector is handled in DB (tsvector)
    search_vector = Column(TSVECTOR)