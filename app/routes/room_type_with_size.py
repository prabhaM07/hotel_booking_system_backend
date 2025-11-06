from fastapi import APIRouter, Depends, Form, File, HTTPException, UploadFile
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.dependency import get_db
from app.core.dependency import get_current_user
from app.models.user import Users
from app.models.room_type import RoomTypeWithSizes
from app.models.bed_type import BedTypes
from app.models.features import Features
from app.models.roomType_bedType import RoomTypeBedTypes
from app.schemas.room_type_schema import  RoomTypeResponse
from app.models.associations import room_type_features
from app.crud.generic_crud import insert_record, delete_record, get_record, save_images,get_record_by_id,update_record,commit_db

router = APIRouter(prefix="/roomtype", tags=["Room Types"])

@router.post("/add",response_model=RoomTypeResponse)
async def add_room_type(
    room_name: str = Form(...),
    base_price_per_night: int = Form(...),
    no_of_adult: int = Form(...),
    no_of_child: int = Form(...),
    feature_ids : Optional[List[str]] = Form(...),
    bed_type_id_with_count : Optional[List[str]] = Form(...),
    images: Optional[List[UploadFile]] = File(None),
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user)
):
    """
    Add a new room type with one or more images.
    """
    image_urls = []
    if images:
        sub_static_dir="feature_images"
        image_urls = await save_images(images,sub_static_dir)
        room_type_data = RoomTypeResponse(
        room_name = room_name,
        base_price = base_price_per_night,
        no_of_adult = no_of_adult,
        no_of_child = no_of_child,
        )
    
    data = await insert_record(
        model=RoomTypeWithSizes,
        db=db,
        **room_type_data.model_dump(),
        images = image_urls
    )
    
    if bed_type_id_with_count:
        room_type_bed_type = []
        for btwc in bed_type_id_with_count:
            
            dicts = {}
            bed_type_id, count = btwc.split(":")
            
            count = int(count)
            
            bed_type_instance = await get_record(db = db,model = BedTypes,id = int(bed_type_id))
            
            if not bed_type_instance:
                raise HTTPException(status_code=404, detail="Bed type not found")
            
            dicts["bed_type_id"] = bed_type_instance.id
            dicts["num_of_beds"] = count
            dicts["room_type_id"] = data.id
            
            room_type_bed_type.append(dicts)
        
    if feature_ids:  
        feature_ids = feature_ids[0].split(',')
        
        for feature_id in feature_ids:
            print(feature_id)
            feature_instance = await get_record(db = db,model = Features,id = int(feature_id))
            
            if not feature_instance:
                raise HTTPException(status_code=404, detail="Feature not found.")

            db.execute(room_type_features.insert().values(room_type_id = data.id,feature_id = feature_instance.id))
        
   
        
    for item in room_type_bed_type:
        await insert_record(db=db, model=RoomTypeBedTypes, **item)
        
    commit_db(db=db)  
    return data

@router.post("/update")
async def update_room_type(
    room_type_id: int = Form(...),
    room_name: Optional[str] = Form(None),
    base_price_per_night: Optional[int] = Form(None),
    no_of_adult: Optional[int] = Form(None),
    no_of_child: Optional[int] = Form(None),
    features: Optional[List[str]] = Form(None),
    bed_types_with_count: Optional[List[str]] = Form(None),
    images: Optional[List[UploadFile]] = File(None),
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user)
):
    """Update existing room type and its related associations."""
    
    # Fetch existing record
    room_type = await get_record_by_id(model = RoomTypeWithSizes,db = db,id = room_type_id)
    if not room_type:
        raise HTTPException(status_code=404, detail="Room type not found")

    # Collect updatable fields
    update_data = {}
    if room_name != "string":
        update_data["room_name"] = room_name
    if base_price_per_night:
        update_data["base_price"] = base_price_per_night
    if no_of_adult:
        update_data["no_of_adult"] = no_of_adult
    if no_of_child:
        update_data["no_of_child"] = no_of_child

    # Handle image updates
    if images:
        sub_static_dir = "feature_images"
        image_urls = await save_images(images, sub_static_dir)
        update_data["images"] = image_urls

   
    # ----- Update Features -----

    if features:  
        features = features[0].split(',')
        # Remove existing relations
        db.execute(room_type_feature.delete().where(room_type_feature.c.room_type_id == room_type_id))
        db.commit()
        
        for feature in features:
            print(feature)
            feature = await get_record(db = db,model = Features,feature_name = feature)
            if not feature:
                raise HTTPException(status_code=404, detail="Feature not found.")

            db.execute(room_type_feature.insert().values(room_type_id = room_type_id,feature_id = feature.id))
        
            db.commit()
        


    # ----- Update Bed Types -----
    
    if bed_types_with_count != ['string']:
        print(bed_types_with_count)
        # Expecting something like ["King:2", "Queen:1"]
        await delete_record(model = RoomTypeBedTypes,db =db,id=room_type_id)

        room_type_bed_type = []
        for btwc in bed_types_with_count:
            
            dicts = {}
            bed_type_name, count = btwc.split(":")
            
            count = int(count)
            bed_type = await get_record(db = db,model = BedTypes,bed_type_name = bed_type_name)
            if not bed_type:
                raise HTTPException(status_code=404, detail="Bed type not found")
            dicts["bed_type_id"] = bed_type.id
            dicts["num_of_beds"] = count
            dicts["room_type_id"] = room_type_id
            
            room_type_bed_type.append(dicts)


    if update_data:
        updated_instance = await update_record(model = RoomTypeWithSizes,db = db, id = room_type_id,**update_data)


    # Refresh and return updated record
    db.refresh(room_type)
    return room_type

