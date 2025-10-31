# app/schemas/ratings_reviews.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime


class RatingsReviewsResponse(BaseModel):
    """Response model for Ratings and Reviews"""
    id: str = Field(..., alias="_id", description="MongoDB ObjectId")
    booking_id: int
    ratings: int
    review: str
    created_at: datetime

    class Config:
        populate_by_name = True
        from_attributes = True


class RatingsReviewsBase(BaseModel):
    """Base model for creating/updating Ratings and Reviews"""
    booking_id: int = Field(
        ...,
        alias="bookingId",
        description="Foreign key reference to Booking table (PostgreSQL).",
        example=1
    )
    ratings: int = Field(
        ...,
        alias="ratings",
        description="Rating value (1-5 stars).",
        example=5
    )
    review: str = Field(
        ...,
        alias="review",
        description="Review text (10-2000 characters).",
        example="Excellent service and clean rooms. Highly recommended!"
    )

    # Validators
    @field_validator("booking_id")
    def validate_booking_id(cls, v):
        if v <= 0:
            raise ValueError("Booking ID must be a positive integer.")
        return v

    @field_validator("ratings")
    def validate_ratings(cls, v):
        if v < 1 or v > 5:
            raise ValueError("Rating must be between 1 and 5.")
        return v

    @field_validator("review")
    def validate_review(cls, v):
        v = v.strip()
        if not (10 <= len(v) <= 2000):
            raise ValueError("Review must be between 10 and 2000 characters long.")
        if not v:
            raise ValueError("Review cannot be empty or whitespace only.")
        return v

    class Config:
        populate_by_name = True


class RatingsReviewsCreate(RatingsReviewsBase):
    """Model for creating a new Rating and Review"""
    pass


class RatingsReviewsUpdate(BaseModel):
    """Model for updating an existing Rating and Review (all fields optional)"""
    booking_id: Optional[int] = Field(
        None,
        alias="bookingId",
        description="Foreign key reference to Booking table.",
        example=2
    )
    ratings: Optional[int] = Field(
        None,
        alias="ratings",
        description="Rating value (1-5 stars).",
        example=4
    )
    review: Optional[str] = Field(
        None,
        alias="review",
        description="Review text.",
        example="Great experience overall!"
    )

    # Reuse validators from base class
    @field_validator("booking_id")
    def validate_booking_id(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Booking ID must be a positive integer.")
        return v

    @field_validator("ratings")
    def validate_ratings(cls, v):
        if v is not None and (v < 1 or v > 5):
            raise ValueError("Rating must be between 1 and 5.")
        return v

    @field_validator("review")
    def validate_review(cls, v):
        if v is not None:
            v = v.strip()
            if not (10 <= len(v) <= 2000):
                raise ValueError("Review must be between 10 and 2000 characters long.")
            if not v:
                raise ValueError("Review cannot be empty or whitespace only.")
        return v

    class Config:
        populate_by_name = True


class RatingsReviewsInDB(RatingsReviewsBase):
    """Model representing a Rating and Review document in MongoDB"""
    id: str = Field(..., alias="_id", description="MongoDB ObjectId as string")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        from_attributes = True