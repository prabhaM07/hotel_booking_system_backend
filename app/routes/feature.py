from typing import Optional
from fastapi import APIRouter, Depends, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.schemas.features_schema import FeatureSchema
from app.models.features import Feature
from app.models.user import User
from app.core.dependency import get_current_user
from app.crud.common_crud import upsert_records,delete_records,get_records
from app.core.dependency import get_db

router = APIRouter(prefix="/feature", tags=["Features"])

@router.post("/add", response_model=FeatureSchema)
async def add_feature(
    feature_name: str = Form(...),
    image: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    feature_data = FeatureSchema(feature_name=feature_name)
    
    new_feature = await upsert_records(
        db=db,
        model=Feature,
        data=feature_data,
        image=image,
        path="feature_images",
        feature_name=feature_name 
    )

    return new_feature

@router.post("/update/image", response_model=FeatureSchema)
async def update_feature_image(
    feature_name: str = Form(...),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    feature_data = FeatureSchema(feature_name=feature_name)
    
    new_feature = await upsert_records(
        db=db,
        model=Feature,
        data=feature_data,
        image=image,
        path="feature_images",
        feature_name=feature_name 
    )

    return new_feature

@router.delete("/delete", response_model=FeatureSchema)
async def delete_feature(
    feature_name: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    feature_data = FeatureSchema(feature_name=feature_name)
    
    await delete_records(
        db=db,
        model=Feature,
        data=feature_data,
        feature_name=feature_name 
    )

    return {"message": "User deleted successfully"}


@router.get("/get")
async def get_feature(
    feature_name: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):    
    return await get_records(
        db=db,
        model=Feature,
        feature_name=feature_name 
    )


