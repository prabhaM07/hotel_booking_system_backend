from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Form
from sqlalchemy import String, Text, func, text
from sqlalchemy.orm import Session
from datetime import datetime
from app.models.Enum import RoomStatusEnum
from app.models.rooms import Rooms
from app.models.user import Users
from app.models.room_status_history import RoomStatusHistory
from app.schemas.rooms_schema import RoomsBase
from app.core.dependency import get_db, get_current_user
from app.crud.generic_crud import insert_record,update_record,get_record,get_record_by_id,delete_record,filter_record,search
from app.schemas.status_history_schema import RoomStatusHistoryBase
router = APIRouter(prefix="/room", tags=["Rooms"])


@router.post("/add")
async def add_room(
    room_type_id: int = Form(...),
    floor_id: int = Form(...),
    room_no: int = Form(...),
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    """Add a new room record"""
    room_base = RoomsBase(
        room_type_id=room_type_id,
        floor_id=floor_id,
        room_no=room_no,
        status=RoomStatusEnum("available"),
    )
    room_data = await insert_record(db=db, model=Rooms, **room_base.model_dump())
    return room_data


@router.post("/update")
async def update_room(
    room_id: int = Form(...),
    room_type_id: Optional[int] = Form(None),
    floor_id: Optional[int] = Form(None),
    room_no: Optional[int] = Form(None),
    status: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    """Update room details"""
    # Step 1: Fetch existing room
    existing_room = await get_record_by_id(model = Rooms,db = db,id = room_id)
    update_data = {}
    if not existing_room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    old_status = existing_room.status
    if status != "string":
        try:
            # Convert to lowercase and validate against the Enum
            
            new_status = RoomStatusEnum(status.lower()) if status else old_status
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid room status: {status}")
        update_data["status"] = new_status
    else:
        new_status = existing_room.status
        
    if status and new_status != old_status:
        history_entry = RoomStatusHistoryBase(
            room_id=id,
            old_status=old_status,
            new_status=new_status
        )
        await insert_record(db=db, model=RoomStatusHistory, **history_entry.model_dump())
    
    if floor_id > 0:
      update_data["floor_id"] = floor_id
    if room_type_id > 0:
      update_data["room_type_id"] = room_type_id
    if room_no > 0:
      update_data["room_no"] = room_no
    
    # Step 4: Update the room record
    
    room_data = await update_record(id=id,db=db, model=Rooms,**update_data)
  
    return room_data


@router.delete("/delete")
async def delete_room(
    room_id: int = Form(...),
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    
    deleted_data = await delete_record(db=db, model=Rooms, id=room_id)
    return deleted_data


@router.get("/get")
async def get_room(
    room_no: Optional[int] = Query(None),
    floor_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user)
):
    """Fetch room records by filters"""
    filters = {}
    if room_no is not None:
        filters["room_no"] = room_no
    if floor_id is not None:
        filters["floor_id"] = floor_id
    if status is not None:
        filters["status"] = status

    return await get_record(db=db, model=Rooms, **filters)

@router.get("/filter")
async def filter_room(
    room_no : Optional[int] = Query(None),
    status : Optional[str] = Query(None),
    created_from : Optional[datetime] = Query(None),
    created_to : Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user)
):
    valid_values = [e.value for e in RoomStatusEnum]
    
    if status not in valid_values:
        raise HTTPException(status_code=400, detail=f"Invalid status . Must be one of {valid_values}.")

    dicts = {}
    if room_no:
        dicts["room_no"] = ["==",room_no]
    if  status:
        dicts["status"]  = ["==",status]
    if created_from:
        dicts["created_at"] = [">=",created_from]
    if created_to:
        dicts["created_at"] = ["<=",created_to]
        
    result = await filter_record(db=db,model= Rooms,**dicts)
    return result



@router.get("/search")
def search_rooms(
    q: str = Query(..., min_length=1),
    page: int = 1,
    per_page: int = 10, 
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user)
):

    result = search(db=db, model=Rooms, q=q, page=page, per_page=per_page)
    return result

