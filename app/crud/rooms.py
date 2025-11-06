
# -------------------- CHECK AVAILABILITY -------------------------
from datetime import date, timedelta
from typing import Type
from app.crud.generic_crud import get_records
from fastapi import HTTPException
from requests import Session
from app.models.Enum import BookingStatusEnum
from app.models.bookings import Bookings
from app.models.rooms import Rooms
from app.models.room_type import RoomTypeWithSizes
from sqlalchemy.exc import SQLAlchemyError


def check_availability(model: Type, db: Session,**kwargs):
    room_id = kwargs.get('room_id')
    check_in = kwargs.get('check_in')
    check_out = kwargs.get('check_out')
    
    if not (room_id and check_in and check_out):
        raise ValueError("room_id, check_in, and check_out are required")
    
    overlap_booking = db.query(model).filter(
        model.room_id == room_id,
        model.check_in < check_out,
        model.check_out > check_in,
        model.booking_status == BookingStatusEnum.CONFIRMED.value
    ).first()

    return overlap_booking is None
    
#-------------------- AVAILABLE DATE TO BOOK FOR A ROOM --------------------
def available_date_of_room(room_id : int,model: Type, db: Session):
    
    today = date.today()
    future_limit = today + timedelta(days=90) 
    
    room_booked_insances = db.query(model).filter(model.room_id == room_id , model.check_out >= today).all()
    
    
    all_dates = set()
    current_date = today

    while current_date <= future_limit:
        all_dates.add(current_date)
        current_date += timedelta(days=1)

    booked_dates = set()
    for rb in room_booked_insances:
        current_date = max(rb.check_in, today)
        while current_date < rb.check_out: 
            booked_dates.add(current_date)
            current_date += timedelta(days=1)
   
    available_dates = sorted(list(all_dates - booked_dates))

    if not available_dates:
        raise HTTPException(status_code=404, detail="No available dates found for this room")

    return {
        "room_id": room_id,
        "from": str(today),
        "to": str(future_limit),
        "available_dates": [str(d) for d in available_dates]
    }
      

#-------------------- AVAILABLE ROOMS ----------------------
def available_rooms(db: Session, check_in: date, check_out: date, no_of_child: int, no_of_adult: int):
    try:
        if check_in >= check_out:
            raise HTTPException(status_code=400, detail="Invalid date range")

        # Find booked rooms in the given period
        booked_room = (
            db.query(Bookings)
            .join(Rooms, Bookings.room_id == Rooms.id)
            .join(RoomTypeWithSizes, Rooms.room_type_id == RoomTypeWithSizes.id)
            .filter(
                Bookings.check_in < check_out,
                Bookings.check_out > check_in,
                RoomTypeWithSizes.no_of_adult >= no_of_adult,
                RoomTypeWithSizes.no_of_child >= no_of_child
            )
            .distinct()
            .all()
        )

        # Safely extract room IDs
        booked_room_ids = [r.room_id for r in booked_room]

        # Fetch rooms not booked in that range
        available_rooms_list = db.query(Rooms).filter(Rooms.id.notin_(booked_room_ids)).all()

        return {
            "available_rooms": [room.id for room in available_rooms_list],
            "count": len(available_rooms_list)
        }

    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

    
    