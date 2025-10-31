from fastapi import APIRouter, Depends, Form, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.core.dependency import get_db
from app.core.dependency import get_current_user
from app.models.user import User
from app.models.bed_type import BedType
from app.schemas.bed_type_schema import BedTypeSchema
from app.crud.common_crud import upsert_records, delete_records, get_records

router = APIRouter(prefix="/bedtype", tags=["Bed Types"])


#  Add new bed type
@router.post("/add", response_model=BedTypeSchema)
async def add_bed_type(
    bed_type_name: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    bed_data = BedTypeSchema(bed_type_name=bed_type_name)

    new_bed_type = await upsert_records(
        db=db,
        model=BedType,
        data=bed_data,
        bed_type_name=bed_type_name
    )
    return new_bed_type


#  Delete bed type
@router.delete("/delete")
async def delete_bed_type(
    bed_type_name: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    bed_data = BedTypeSchema(bed_type_name=bed_type_name)

    await delete_records(
        db=db,
        model=BedType,
        data=bed_data,
        bed_type_name=bed_type_name
    )

    return {"message": f"Bed type '{bed_type_name}' deleted successfully"}


#  Get bed type(s)
@router.get("/get")
async def get_bed_type(
    bed_type_name: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Fetch all bed types or a specific one if `bed_type_name` is provided.
    """
    if bed_type_name:
        return await get_records(db=db, model=BedType, bed_type_name=bed_type_name)
    return await get_records(db=db, model=BedType)
