# app/crud/room_type_feature_crud.py

from typing import Dict, List
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.associations import room_type_feature
from app.models.features import Feature
from app.models.bed_type import BedType
from app.models.roomType_bedType import RoomTypeBedType

async def update_Room_Type_Feature(db: Session, room_type_id: int, features: List[str] = None):
    """
    Updates the room_type_feature association table for a given Room Type.
    - Finds feature IDs by their names.
    - Inserts new rows into the association table.
    """

    if not features:
        return

    # Find all matching feature IDs for given feature names
    feature_objs = db.query(Feature).filter(Feature.feature_name.in_(features)).all()
    if not feature_objs:
        return

    feature_ids = [f.id for f in feature_objs]

    # Clear existing associations (if needed)
    db.execute(
        room_type_feature.delete().where(room_type_feature.c.room_type_id == room_type_id)
    )

    # Insert new associations
    insert_values = [
        {"room_type_id": room_type_id, "feature_id": fid} for fid in feature_ids
    ]
    
    if insert_values:
        db.execute(room_type_feature.insert(), insert_values)
    

    db.commit()
    

async def update_Room_Type_Bed_Type(
    db: Session, 
    room_type_id: int, 
    bed_types_with_count: Dict = None
):
    """
    Updates RoomTypeBedType associations for a room type.
    - Deletes old associations.
    - Inserts new ones using the provided dict {bed_type_name: num_of_beds}.
    Example:
        bed_types_with_count = {"King Bed": 2, "Queen Bed": 1}
    """

    if not bed_types_with_count:
        return
    print(1)
    #  Remove existing entries for this room type
    db.query(RoomTypeBedType).filter(
        RoomTypeBedType.room_type_id == room_type_id
    ).delete()

    #  For each (bed_type_name, num_of_beds), find bed_type_id and insert new link
    for bed_name, count in bed_types_with_count.items():
        bed_obj = db.query(BedType).filter(func.lower(BedType.bed_type_name) == func.lower(bed_name)).first()

        if not bed_obj:
            # Optional: skip or raise exception if bed type not found
            print(f"Skipping unknown bed type: {bed_name}")
            continue

        new_assoc = RoomTypeBedType(
            room_type_id=room_type_id,
            bed_type_id=bed_obj.id,
            num_of_beds=count
        )
        db.add(new_assoc)

    db.commit()

    
    