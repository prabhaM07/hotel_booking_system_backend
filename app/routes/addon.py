from typing import Optional
from fastapi import APIRouter, Depends, Query, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from app.schemas.addon_schema import AddonSchema
from app.models.addon import Addons
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

router = APIRouter(prefix="/addon", tags=["Addons"])


# --------------------- ADD ADDON ---------------------
@router.post("/add", response_model=AddonSchema)
async def add_addon(
    addon_name: str = Form(...),
    base_price: int = Form(...),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sub_static_dir = "addon_images"
    image_url = await save_image(image, sub_static_dir) if image else None

    addon_data = AddonSchema(
        addon_name=addon_name,
        base_price=base_price,
        image=image_url,
    )
    new_addon = await insert_record(
        db=db,
        model=Addons,
        **addon_data.model_dump(),
    )

    return new_addon


# --------------------- UPDATE IMAGE ---------------------
@router.post("/update/image", response_model=AddonSchema)
async def update_addon_image(
    addon_id: int = Form(...),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    instance = await get_record(model=Addons, db=db, id=addon_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Addon not found")

    if image:
        # Delete old image if exists
        existing_image = instance.image
        if existing_image:
            image_path = os.path.join("app", existing_image)
            if os.path.exists(image_path):
                os.remove(image_path)

        # Save new image
        sub_static_dir = "addon_images"
        image_url = await save_image(image, sub_static_dir)

        updated_addon = await update_record(
            id=addon_id,
            model=Addons,
            db=db,
            image=image_url,
        )
        return updated_addon

    return instance


# --------------------- UPDATE BASE DETAILS ---------------------
@router.post("/update/details", response_model=AddonSchema)
async def update_addon_details(
    addon_id: int = Form(...),
    addon_name: Optional[str] = Form(None),
    base_price: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    instance = await get_record(model=Addons, db=db, id=addon_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Addon not found")

    updated_data = {}
    if addon_name:
        updated_data["addon_name"] = addon_name
    if base_price is not None:
        updated_data["base_price"] = base_price

    updated_addon = await update_record(
        id=addon_id,
        model=Addons,
        db=db,
        **updated_data,
    )

    return updated_addon


# --------------------- DELETE ADDON ---------------------
@router.delete("/delete")
async def delete_addon(
    addon_id: int = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    deleted_addon = await delete_record(
        id=addon_id,
        model=Addons,
        db=db,
    )
    return {"message": f"Addon with ID {addon_id} deleted successfully"}


# --------------------- GET ADDON ---------------------
@router.get("/get", response_model=AddonSchema)
async def get_addon(
    addon_name: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    addon = await get_record(model=Addons, db=db, addon_name=addon_name)
    if not addon:
        raise HTTPException(status_code=404, detail="Addon not found")
    return addon
