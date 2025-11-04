from datetime import date, timedelta
from typing import List, Optional
from fastapi import APIRouter, Body, Depends, HTTPException, Query, Form
from sqlalchemy.orm import Session
from datetime import datetime
from app.models.Enum import BookingStatusEnum,PaymentStatusEnum , RefundStatusEnum,RoomStatusEnum
from app.models.reschedule import Reschedule
from app.models.rooms import Rooms
from app.models.user import User
from app.models.bookings import Bookings
from app.models.booking_status_history import BookingStatusHistory
from app.models.rooms import Rooms
from app.models.room_type import RoomTypeWithSize
from app.models.payment import Payments
from app.models.refund import Refunds
from app.models.addon import Addons
from app.models.booking_addon import BookingAddon
from app.schemas.payment_schema import PaymentBase
from app.schemas.status_history_schema import BookingStatusHistoryBase
from app.schemas.booking_schema import BookingBase
from app.core.dependency import get_db, get_current_user
from app.crud.generic_crud import insert_record,get_record,get_record_by_id,insert_record_flush,commit_db
from app.crud.rooms import available_rooms,available_date_of_room,check_availability

router = APIRouter(prefix="/booking", tags=["Bookings"])

@router.post("/add")
async def book_room(
    booking: BookingBase,
    addon_list: Optional[List[str]] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a new room record"""
    room_instance = await get_record_by_id(db=db,model = Rooms,id = booking.room_id)
    root_type_instance = await get_record_by_id(db=db,model = RoomTypeWithSize,id = room_instance.room_type_id)
    
    available = check_availability(db=db,model=Bookings,check_in = booking.check_in,check_out = booking.check_out,room_id = booking.room_id)
    
    if not available:
        raise ValueError("The request room is not available at this date")
    
    from_date = booking.check_in
    to_date = booking.check_out
    
    no_of_days = (to_date - from_date).days
    room_amount = no_of_days * root_type_instance.base_price

    
    booking_instance = await insert_record_flush(db=db, model=Bookings, **booking.model_dump(),total_amount = room_amount)
    
    addon_amount = 0
    
    if addon_list != ["string"] and len(addon_list) > 0:
        for addon in addon_list:
            
            addon_id, quantity = addon.split(':')
            
            instance = await get_record_by_id(db=db,model=Addons,id = addon_id)
            addon_amount += instance.base_price
            
            dicts = {}
            
            dicts["booking_id"] = booking_instance.id
            dicts["addon_id"] = addon_id
            dicts["quantity"] = quantity
            
            await insert_record(db=db , model= BookingAddon , **dicts)
            
    total_amount = room_amount + addon_amount
    
    pament_data_base = PaymentBase(
        booking_id= booking_instance.id,
        total_amount= total_amount,
        status= PaymentStatusEnum.PAID.value
    )
    
    await insert_record(db = db,model=Payments,**pament_data_base.model_dump())
    
    await commit_db(db)
    
    result = await get_record_by_id(db=db, model=Bookings,id = booking_instance.id)

    return result


@router.post("/cancel")
async def cancel_booking(
    booking_id: int = Form(...),
    reason : str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    existing_booking = db.query(Bookings).filter(Bookings.id == booking_id).first()
    
    if not existing_booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    status = BookingStatusEnum(existing_booking.booking_status.lower())
    if  status != "confirmed":
        raise HTTPException(status_code=404, detail="Cancelling the booking is not accepted")
    
    existing_booking.booking_status =  BookingStatusEnum.CANCELLED.value
    total_Amount = existing_booking.total_amount
    
    # Cancel ≥ 7 days before check-in → 100% refund

    # Cancel 3–6 days before → 50% refund

    # Cancel < 3 days before → No refund
    
    no_days = (existing_booking.check_in - date.today()).days
    
    refund_amount = 0
    
    message = ""
    flag = 1
    if no_days < 3:
        flag = 0
        message =  "Cancellation request failed. Cancel before 3 days of check in date"
    
    if no_days <= 6 and no_days >= 3:
        
        refund_amount = total_Amount / 2
        message =  f"refund amount {refund_amount} will be send after 2 days"

    if no_days >= 7:
        
        refund_amount = total_Amount
        message =  f"refund amount {total_Amount} will be send after 2 days"

    payment = await get_record(db=db,model=Payments,booking_id = booking_id)
    
    payment.status = PaymentStatusEnum.REFUNDED.value
    
    
    dicts = {}
    dicts["payment_id"] = payment.id
    if flag :
        dicts["status"] = RefundStatusEnum.APPROVED.value
    else:
        dicts["status"] = RefundStatusEnum.REJECTED.value
    dicts["reason"] = message
    dicts["total_amount"] = total_Amount
    dicts["refund_amount"] = refund_amount
    
    refunded_data = await insert_record(db=db,model=Refunds,**dicts)
    
    status_history = BookingStatusHistoryBase(
        booking_id = booking_id,
        old_status = BookingStatusEnum.CONFIRMED.value,
        new_status = BookingStatusEnum.CANCELLED.value
    )
    
    await insert_record(db=db , model=BookingStatusHistory , **status_history.model_dump())
    
    return refunded_data
    
 
@router.post("/checkAvailability")
async def availabile_date_of_room(
    room_id: int = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    available_dates = available_date_of_room(room_id = room_id,db=db,model=Bookings)
    
    return available_dates


@router.post("/reschedule")
async def reschdule_bookings(
    booking_id : int = Form(...),
    check_in : date = Form(...),
    check_out : date = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    
   
    if check_in >= check_out:
        raise HTTPException(status_code=400, detail="Invalid date range")
    
    booking_instance  = await get_record(id = booking_id , db=db , model=Bookings)
    
    
    if not booking_instance:
        raise HTTPException(status_code=404, detail=f"Booking with ID {booking_id} not found")

    if booking_instance.booking_status != BookingStatusEnum.CONFIRMED:
        raise HTTPException(status_code=400, detail="Cannot reschdule this booking")
    
    
     # --- Rule 1: cutoff days ---
    cutoff_days = 3
    if date.today() > booking_instance.check_in - timedelta(days=cutoff_days):
        raise HTTPException(status_code=400, detail="Too late to reschedule this booking")

    # --- Rule 2: only one reschedule ---
    already_rescheduled = db.query(Reschedule).filter(Reschedule.booking_id == booking_id).first()
    if already_rescheduled:
        raise HTTPException(status_code=400, detail="This booking has already been rescheduled once")

    
    available = check_availability(db=db,model=Bookings,check_in = check_in,check_out = check_out,room_id = booking_instance.room_id)

    if available:
        
        booking_instance.check_in = check_in
        booking_instance.check_out = check_out
        
        return await insert_record(db=db, model=Reschedule, booking_id = booking_id)
    else :
        return available_rooms(model=Bookings,db=db,check_in = check_in,check_out=check_out) 
          