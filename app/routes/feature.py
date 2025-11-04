from typing import Optional
from fastapi import APIRouter, Depends, Query, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from app.schemas.features_schema import FeatureSchema
from app.models.features import Feature
from app.models.user import User
from app.core.dependency import get_current_user, get_db
from app.crud.generic_crud import (
    insert_record,
    update_record,
    delete_record,
    save_image,
    get_record,
)
import os

router = APIRouter(prefix="/feature", tags=["Features"])


# --------------------- ADD FEATURE ---------------------
@router.post("/add", response_model=FeatureSchema)
async def add_feature(
    feature_name: str = Form(...),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sub_static_dir = "feature_images"
    image_url = await save_image(image, sub_static_dir) if image else None

    feature_data = FeatureSchema(
        feature_name=feature_name,
        image=image_url,
    )
    new_feature = await insert_record(
        db=db,
        model=Feature,
        **feature_data.model_dump(),
    )

    return new_feature


# --------------------- UPDATE IMAGE ---------------------
@router.post("/update/image", response_model=FeatureSchema)
async def update_feature_image(
    feature_id: int = Form(...),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    instance = await get_record(model=Feature, db=db, id=feature_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Feature not found")

    if image:
        # Delete old image if exists
        existing_image = instance.image
        if existing_image:
            image_path = os.path.join("app", existing_image)
            if os.path.exists(image_path):
                os.remove(image_path)

        # Save new image
        sub_static_dir = "feature_images"
        image_url = await save_image(image, sub_static_dir)

        updated_feature = await update_record(
            id=feature_id,
            model=Feature,
            db=db,
            image=image_url,
        )
        return updated_feature

    return instance


# --------------------- DELETE FEATURE ---------------------
@router.delete("/delete")
async def delete_feature(
    feature_id: int = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    deleted_feature = await delete_record(
        id=feature_id,
        model=Feature,
        db=db,
    )
    return {"message": f"Feature with ID {feature_id} deleted successfully"}


# --------------------- GET FEATURE ---------------------
@router.get("/get", response_model=FeatureSchema)
async def get_feature(
    feature_name: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    feature = await get_record(model=Feature, db=db, feature_name=feature_name)
    if not feature:
        raise HTTPException(status_code=404, detail="Feature not found")
    return feature
