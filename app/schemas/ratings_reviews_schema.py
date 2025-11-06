from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator

class RatingsReviewsBase(BaseModel):
    """Base model for creating/updating Ratings and Reviews"""
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
        