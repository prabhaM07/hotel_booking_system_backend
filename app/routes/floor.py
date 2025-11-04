from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, Form
from sqlalchemy.orm import Session
from app.schemas.floor_schema import FloorBase
from app.models.floor import Floor
from app.models.user import User
from app.core.dependency import get_current_user, get_db
from app.crud.generic_crud import insert_record, update_record, delete_record, get_record

router = APIRouter(prefix="/floor", tags=["Floors"])


# ------------------ ADD FLOOR ------------------
@router.post("/add", response_model=FloorBase)
async def add_floor(
    floor_no: int = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    floor_data = FloorBase(floorNo=floor_no)

    new_floor = await insert_record(
        db=db,
        model=Floor,
        **floor_data.model_dump(),
    )
    return new_floor


# ------------------ DELETE FLOOR ------------------
@router.delete("/delete", response_model=dict)
async def delete_floor(
    floor_no: int = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Find the record first
    record = await get_record(
        db=db,
        model=Floor,
        floor_no=floor_no
    )

    if not record:
        raise HTTPException(status_code=404, detail=f"Floor {floor_no} not found")

    await delete_record(
        db=db,
        model=Floor,
        id=record.id
    )

    return {"message": f"Floor {floor_no} deleted successfully"}


# ------------------ GET FLOOR ------------------
@router.get("/get", response_model=FloorBase)
async def get_floor(
    floor_no: int = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = await get_record(
        db=db,
        model=Floor,
        floor_no=floor_no
    )

    if not record:
        raise HTTPException(status_code=404, detail=f"Floor {floor_no} not found")

    return record
