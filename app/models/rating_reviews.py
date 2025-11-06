from sqlalchemy import Column, ForeignKey, String, DateTime, func, Integer
from app.core.database_postgres import Base
from sqlalchemy.orm import relationship
from app.models.associations import room_type_features


class RatingsReviews(Base):
    __tablename__ = "ratings_reviews"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    booking_id = Column(
        Integer,
        ForeignKey("bookings.id", ondelete="CASCADE"),
        nullable=False
    )
    room_id = Column(
        Integer,
        ForeignKey("rooms.id", ondelete="CASCADE"),
        nullable=False
    )
    odject_id = Column(
      String,
      nullable=False
    )
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    booking = relationship(
        "Bookings",
        back_populates="ratingReview",
        lazy="joined"
    )
    
    room = relationship(
        "Rooms",
        back_populates="ratingReview",
        lazy="joined"
    )
   