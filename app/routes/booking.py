from datetime import date, timedelta
from typing import List, Optional
from fastapi import APIRouter, Body, Depends, HTTPException, Query, Form
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from app.models.Enum import BookingStatusEnum, PaymentStatusEnum, RefundStatusEnum, RoomStatusEnum
from app.models.reschedule import Reschedule
from app.models.rooms import Rooms
from app.models.user import User
from app.models.bookings import Bookings
from app.models.booking_status_history import BookingStatusHistory
from app.models.room_type import RoomTypeWithSize
from app.models.payment import Payments
from app.models.refund import Refunds
from app.models.addon import Addons
from app.models.booking_addon import BookingAddon
from app.schemas.payment_schema import PaymentBase
from app.schemas.status_history_schema import BookingStatusHistoryBase
from app.schemas.booking_schema import BookingBase
from app.core.dependency import get_db, get_current_user
from app.crud.generic_crud import insert_record, get_record, get_record_by_id, insert_record_flush, commit_db
from app.crud.rooms import available_rooms, available_date_of_room, check_availability

router = APIRouter(prefix="/booking", tags=["Bookings"])


@router.post("/add")
async def book_room(
    booking: BookingBase,
    addon_list: Optional[List[str]] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a new room record"""
    try:
        room_instance = await get_record_by_id(db=db, model=Rooms, id=booking.room_id)
        if not room_instance:
            raise HTTPException(status_code=404, detail="Room not found")

        root_type_instance = await get_record_by_id(db=db, model=RoomTypeWithSize, id=room_instance.room_type_id)
        if not root_type_instance:
            raise HTTPException(status_code=404, detail="Room type not found")

        available = check_availability(
            db=db, model=Bookings, check_in=booking.check_in, check_out=booking.check_out, room_id=booking.room_id
        )

        if not available:
            raise HTTPException(status_code=400, detail="The requested room is not available for this date")

        from_date = booking.check_in
        to_date = booking.check_out
        no_of_days = (to_date - from_date).days
        room_amount = no_of_days * root_type_instance.base_price

        booking_instance = await insert_record_flush(
            db=db, model=Bookings, **booking.model_dump(), total_amount=room_amount
        )

        addon_amount = 0
        if addon_list and addon_list != ["string"]:
            for addon in addon_list:
                try:
                    addon_id, quantity = addon.split(':')
                except ValueError:
                    raise HTTPException(status_code=400, detail=f"Invalid addon format: {addon}")

                instance = await get_record_by_id(db=db, model=Addons, id=addon_id)
                if not instance:
                    raise HTTPException(status_code=404, detail=f"Addon with ID {addon_id} not found")

                addon_amount += instance.base_price

                dicts = {
                    "booking_id": booking_instance.id,
                    "addon_id": addon_id,
                    "quantity": quantity
                }
                await insert_record(db=db, model=BookingAddon, **dicts)

        total_amount = room_amount + addon_amount
        payment_data_base = PaymentBase(
            booking_id=booking_instance.id,
            total_amount=total_amount,
            status=PaymentStatusEnum.PAID.value
        )

        await insert_record(db=db, model=Payments, **payment_data_base.model_dump())
        await commit_db(db)

        result = await get_record_by_id(db=db, model=Bookings, id=booking_instance.id)
        if not result:
            raise HTTPException(status_code=500, detail="Failed to fetch booking after creation")

        return result

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.post("/cancel")
async def cancel_booking(
    booking_id: int = Form(...),
    reason: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        existing_booking = db.query(Bookings).filter(Bookings.id == booking_id).first()
        if not existing_booking:
            raise HTTPException(status_code=404, detail="Booking not found")

        status = BookingStatusEnum(existing_booking.booking_status.lower())
        if status != BookingStatusEnum.CONFIRMED:
            raise HTTPException(status_code=400, detail="Only confirmed bookings can be cancelled")

        existing_booking.booking_status = BookingStatusEnum.CANCELLED.value
        total_Amount = existing_booking.total_amount

        no_days = (existing_booking.check_in - date.today()).days
        refund_amount = 0
        message = ""
        flag = 1

        if no_days < 3:
            flag = 0
            message = "Cancellation request failed. Cancel before 3 days of check-in date"
        elif 3 <= no_days <= 6:
            refund_amount = total_Amount / 2
            message = f"Refund amount {refund_amount} will be sent after 2 days"
        elif no_days >= 7:
            refund_amount = total_Amount
            message = f"Refund amount {total_Amount} will be sent after 2 days"

        payment = await get_record(db=db, model=Payments, booking_id=booking_id)
        if not payment:
            raise HTTPException(status_code=404, detail="Payment record not found")

        payment.status = PaymentStatusEnum.REFUNDED.value

        dicts = {
            "payment_id": payment.id,
            "status": RefundStatusEnum.APPROVED.value if flag else RefundStatusEnum.REJECTED.value,
            "reason": message,
            "total_amount": total_Amount,
            "refund_amount": refund_amount
        }

        refunded_data = await insert_record(db=db, model=Refunds, **dicts)

        status_history = BookingStatusHistoryBase(
            booking_id=booking_id,
            old_status=BookingStatusEnum.CONFIRMED.value,
            new_status=BookingStatusEnum.CANCELLED.value
        )

        await insert_record(db=db, model=BookingStatusHistory, **status_history.model_dump())
        await commit_db(db)

        return refunded_data

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.post("/checkAvailability")
async def availabile_date_of_room(
    room_id: int = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        available_dates = available_date_of_room(room_id=room_id, db=db, model=Bookings)
        if not available_dates:
            raise HTTPException(status_code=404, detail="No availability data found")
        return available_dates
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.post("/reschedule")
async def reschdule_bookings(
    booking_id: int = Form(...),
    check_in: date = Form(...),
    check_out: date = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        if check_in >= check_out:
            raise HTTPException(status_code=400, detail="Invalid date range")

        booking_instance = await get_record(id=booking_id, db=db, model=Bookings)
        if not booking_instance:
            raise HTTPException(status_code=404, detail=f"Booking with ID {booking_id} not found")

        if booking_instance.booking_status != BookingStatusEnum.CONFIRMED:
            raise HTTPException(status_code=400, detail="Cannot reschedule this booking")

        cutoff_days = 3
        if date.today() > booking_instance.check_in - timedelta(days=cutoff_days):
            raise HTTPException(status_code=400, detail="Too late to reschedule this booking")

        already_rescheduled = db.query(Reschedule).filter(Reschedule.booking_id == booking_id).first()
        if already_rescheduled:
            raise HTTPException(status_code=400, detail="This booking has already been rescheduled once")

        available = check_availability(
            db=db, model=Bookings, check_in=check_in, check_out=check_out, room_id=booking_instance.room_id
        )

        if available:
            booking_instance.check_in = check_in
            booking_instance.check_out = check_out
            reschedule_record = await insert_record(db=db, model=Reschedule, booking_id=booking_id)
            await commit_db(db)
            return reschedule_record
        else:
            room_instance = await get_record_by_id(db=db,model=Rooms,id = booking_instance.room_id)
            room_type_instance = await get_record_by_id(db=db,model=RoomTypeWithSize,id = room_instance.room_type_id)
            return available_rooms(db=db, check_in=check_in, check_out=check_out,no_of_adult = room_type_instance.no_of_adult,no_of_child=room_type_instance.no_of_child)

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
