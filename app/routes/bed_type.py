from fastapi import APIRouter, Depends, Form, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from app.core.dependency import get_db, get_current_user
from app.models.user import User
from app.models.bed_type import BedType
from app.schemas.bed_type_schema import BedTypeSchema
from app.crud.generic_crud import insert_record, delete_record, get_record_by_id, get_record, update_record

router = APIRouter(prefix="/bedtype", tags=["Bed Types"])


# ------------------ ADD NEW BED TYPE ------------------
@router.post("/add", response_model=BedTypeSchema)
async def add_bed_type(
    bed_type_name: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    bed_data = BedTypeSchema(bed_type_name=bed_type_name)

    new_bed_type = await insert_record(
        db=db,
        model=BedType,
        **bed_data.model_dump(),
    )
    return new_bed_type


# ------------------ DELETE BED TYPE ------------------
@router.delete("/delete")
async def delete_bed_type(
    bed_type_name: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Find the record first
    record = await get_record(
        db=db,
        model=BedType,
        bed_type_name=bed_type_name
    )

    if not record:
        raise HTTPException(status_code=404, detail="Bed type not found")

    await delete_record(
        db=db,
        model=BedType,
        id=record.id
    )

    return {"message": f"Bed type '{bed_type_name}' deleted successfully"}


# ------------------ GET BED TYPE(S) ------------------
@router.get("/get")
async def get_bed_type(
    bed_type_name: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if bed_type_name:
        record = await get_record(db=db, model=BedType, bed_type_name=bed_type_name)
        if not record:
            raise HTTPException(status_code=404, detail="Bed type not found")
        return record

    # Fetch all bed types if no filter provided
    records = await get_record(db=db, model=BedType)
    return records
