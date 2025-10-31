from fastapi import APIRouter, Depends, Form, File, HTTPException, UploadFile,Query
from sqlalchemy.orm import Session,joinedload
from typing import List, Optional,Dict
from app.core.dependency import get_db
from app.core.dependency import get_current_user
from app.models.user import User
from app.models.room_type import RoomTypeWithSize
from app.schemas.room_type_schema import  RoomTypeResponse
from app.crud.common_crud import upsert_records, delete_records, get_records
from app.crud.room_type_with_size import update_Room_Type_Feature,update_Room_Type_Bed_Type

router = APIRouter(prefix="/roomtype", tags=["Room Types"])

@router.post("/add",response_model=RoomTypeResponse)
async def add_room_type(
    room_name: str = Form(...),
    base_price_per_night: int = Form(...),
    no_of_adult: int = Form(...),
    no_of_child: int = Form(...),
    features : Optional[List[str]] = Form(...),
    bed_types_with_count : Optional[List[str]] = Form(...),
    images: Optional[List[UploadFile]] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add a new room type with one or more images.
    """
    
    room_type_data = RoomTypeResponse(
      room_name = room_name,
      base_price = base_price_per_night,
      no_of_adult = no_of_adult,
      no_of_child = no_of_child
    )
    
    bed_types = {}
    
    for btwc in bed_types_with_count:
        
        typee, count = btwc.split(":")
        count = int(count)
        
        bed_types[typee] = count


    data = await upsert_records(
        db=db,
        model=RoomTypeWithSize,
        data=room_type_data,
        image=images,   
        path="room_type_images"
    )
    
    await update_Room_Type_Feature(db,data.id,features)
    await update_Room_Type_Bed_Type(db,data.id,bed_types)
    
    return data


@router.post("/update")
async def update_room_type(
    room_type_id: int = Form(...),
    room_name: Optional[str] = Form(None),
    base_price_per_night: Optional[int] = Form(None),
    no_of_adult: Optional[int] = Form(None),
    no_of_child: Optional[int] = Form(None),
    features: Optional[List[str]] = Form(None),
    bed_types_with_count: Optional[str] = Form(None),
    images: Optional[List[UploadFile]] | None = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update existing room type and its associations."""
    
    room_type = db.query(RoomTypeWithSize).filter(RoomTypeWithSize.id == room_type_id).first()
    if not room_type:
        raise HTTPException(status_code=404, detail="Room type not found")

    update_data = {}
    if room_name:
        update_data["room_name"] = room_name
    if base_price_per_night:
        update_data["base_price"] = base_price_per_night
    if no_of_adult:
        update_data["no_of_adult"] = no_of_adult
    if no_of_child:
        update_data["no_of_child"] = no_of_child

    # Update associations
    if features:
        update_Room_Type_Feature(db, room_type.id, features)
    if bed_types_with_count:
        update_Room_Type_Bed_Type(db, room_type.id, bed_types_with_count)

    # Optionally handle image update via upsert
    if images is not "":
        await upsert_records(
            db=db,
            model=RoomTypeWithSize,
            data=update_data,
            image=images,
            path="room_type_images"
        )
    else:
        db.query(RoomTypeWithSize).filter(RoomTypeWithSize.id == room_type_id).update(update_data)
        db.commit()

    return room_type
    
    
@router.get("/get")
async def get_room_type(
    room_type_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Fetch room type with features and bed types using joined loading.
    """
    res = await get_records(db=db, model=RoomTypeWithSize, id=room_type_id)
    return res
