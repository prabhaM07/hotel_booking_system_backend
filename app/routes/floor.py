from typing import Optional
from fastapi import APIRouter, Depends, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.schemas.floor_schema import FloorBase
from app.models.floor import Floor
from app.models.user import User
from app.core.dependency import get_current_user
from app.crud.common_crud import upsert_records,delete_records,get_records
from app.core.dependency import get_db


router = APIRouter(prefix="/floor",tags = ["Floors"])


@router.post("/add")
async def add_floor(floor_no : int = Form(...),db: Session = Depends(get_db),current_user : User = Depends(get_current_user)):
  floor_base = FloorBase(floorNo=floor_no)
  floor_data = await upsert_records(db = db,model = Floor,data = floor_base)
  return floor_data
  
  

@router.delete("/delete")
async def delete_floor(floor_no : int = Form(...),db: Session = Depends(get_db),current_user : User = Depends(get_current_user)):
  floor_base = FloorBase(floorNo=floor_no)
  floor_data = await delete_records(db = db,model = Floor,data = floor_base)
  return floor_data


@router.get("/get")
async def get_records(
    floor_no: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):    
    return await get_records(
        db=db,
        model=Floor,
        floor_no=floor_no
    )

