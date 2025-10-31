from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Form
from sqlalchemy.orm import Session

from app.models.Enum import RoomStatusEnum
from app.models.rooms import Rooms
from app.models.user import User
from app.models.room_status_history import RoomStatusHistory
from app.schemas.rooms_schema import RoomsBase
from app.core.dependency import get_db, get_current_user
from app.crud.common_crud import upsert_records, delete_records, get_records
from app.schemas.status_history_schema import RoomStatusHistoryBase
router = APIRouter(prefix="/room", tags=["Rooms"])


@router.post("/add")
async def add_room(
    room_type_id: int = Form(...),
    floor_id: int = Form(...),
    room_no: int = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a new room record"""
    room_base = RoomsBase(
        room_type_id=room_type_id,
        floor_id=floor_id,
        room_no=room_no,
        status=RoomStatusEnum("available"),
    )
    room_data = await upsert_records(db=db, model=Rooms, data=room_base)
    return room_data


@router.post("/update")
async def update_room(
    id: int = Form(...),
    room_type_id: Optional[int] = Form(None),
    floor_id: Optional[int] = Form(None),
    room_no: Optional[int] = Form(None),
    status: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update room details"""
    # Step 1: Fetch existing room
    existing_room = db.query(Rooms).filter(Rooms.id == id).first()
    if not existing_room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    if status:
        try:
            # Convert to lowercase and validate against the Enum
            old_status = existing_room.status
            new_status = RoomStatusEnum(status.lower()) if status else old_status
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid room status: {status}")
    else:
        new_status = existing_room.status
        
    if status and new_status != old_status:
        history_entry = RoomStatusHistoryBase(
            room_id=id,
            old_status=old_status,
            new_status=new_status,
            changed_by=current_user.id,
        )
        await upsert_records(db=db, model=RoomStatusHistory, data=history_entry)
        
    room_base = RoomsBase(
        id=id,
        room_type_id=room_type_id,
        floor_id=floor_id,
        room_no=room_no,
        status=new_status,
    )
    
    # Step 4: Update the room record
    
    room_data = await upsert_records(db=db, model=Rooms, data=room_base,id = room_base.id)
    

    return room_data


@router.delete("/delete")
async def delete_room(
    id: int = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    
    deleted_data = await delete_records(db=db, model=Rooms, id=id)
    return deleted_data


@router.get("/get")
async def get_room(
    room_no: Optional[int] = Query(None),
    floor_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetch room records by filters"""
    filters = {}
    if room_no is not None:
        filters["room_no"] = room_no
    if floor_id is not None:
        filters["floor_id"] = floor_id
    if status is not None:
        filters["status"] = status

    return await get_records(db=db, model=Rooms, **filters)
