from typing import Optional
from fastapi import APIRouter, Form, HTTPException,Request,Depends
from sqlalchemy.orm import Session
from app.models.bookings import Bookings
from app.schemas.ratings_reviews_schema import RatingsReviewsBase
from app.models.Enum import BookingStatusEnum
from app.models.rating_reviews import RatingsReviews
from app.utils import convertTOString
from app.core.dependency import get_db
from app.core.database_mongo import db
from app.crud.generic_crud import delete_record_mongo, get_record_by_id, get_record_mongo,insert_record_mongo,insert_record,update_record_mongo

collection = db["ratings_reviews"]

router = APIRouter(prefix="/ratings_reviews", tags=["ratings_reviews"])

@router.post("/add")
async def create_ratings_reviews(booking_id : int ,ratings: RatingsReviewsBase,request: Request,db: Session = Depends(get_db)):
    booking_instance = get_record_by_id(id = booking_id,model = Bookings,db = db)
    
    if booking_instance.booking_status != BookingStatusEnum.COMPLETED.value:
        raise ValueError("The reviews can be enabled only after completing the stay")
    result = await insert_record_mongo(collection=collection,**ratings.model_dump())
    
    dicts = {}
    dicts["booking_id"] = booking_instance.id
    dicts["room_id"] = booking_instance.room_id
    dicts["object_id"] = result["id"]
    
    ratings_reviews_instance = insert_record(db=db,model=RatingsReviews,**dicts)
    
    return ratings_reviews_instance
    

@router.post("/update")
async def update_ratings_reviews(ratings_reviews_id : int ,request: Request,ratings: Optional[int] = Form(None),reviews: Optional[str] = Form(None),db: Session = Depends(get_db)):
    
    ratings_reviews_instance = get_record_by_id(id = ratings_reviews_id,model = RatingsReviews,db = db)
    
    dicts = {}
    dicts["ratings"] = ratings
    dicts["reviews"] = reviews
    
    result = await update_record_mongo(id=ratings_reviews_instance.odject_id,collection=collection,**dicts)
    
    result["id"] = convertTOString(result["_id"])
    return result
    
@router.get("/{id}")
async def get_ratings_reviews(ratings_reviews_id : int, db: Session = Depends(get_db), collection=None):
    
    ratings_reviews_instance = get_record_by_id(id = ratings_reviews_id,model = RatingsReviews,db = db)
    result = await get_record_mongo(id = ratings_reviews_instance.odject_id, collection = collection)
    if not result:
        raise HTTPException(status_code=404, detail="Review not found")
    
    result["id"] = convertTOString(result["_id"])
    return result

@router.delete("/delete/{id}")
async def delete_ratings_reviews(ratings_reviews_id: int, collection=None):
    ratings_reviews_instance = get_record_by_id(id = ratings_reviews_id,model = RatingsReviews,db = db)
    
    result = await delete_record_mongo(id = ratings_reviews_instance.odject_id, collection = collection)
    
    if not result["deleted"]:
        raise HTTPException(status_code=404, detail=result.get("error", "Delete failed"))
    return result

