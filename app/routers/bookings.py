"""Бронирование слотов. Ключевой момент — защита от двойного бронирования
при параллельных запросах: блокировка строки слота (SELECT ... FOR UPDATE)
внутри транзакции + UNIQUE(slot_id) в bookings как second line of defence."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Booking, BookingStatus, Slot, User
from app.schemas import BookingCreate, BookingOut, SlotOut

router = APIRouter(tags=["bookings"])


@router.get("/slots", response_model=list[SlotOut])
def available_slots(
    service_id: int,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Slot).filter(Slot.service_id == service_id, Slot.is_booked.is_(False))
    if date_from:
        query = query.filter(Slot.starts_at >= date_from)
    if date_to:
        query = query.filter(Slot.starts_at <= date_to)
    return query.order_by(Slot.starts_at).all()


@router.post("/bookings", response_model=BookingOut, status_code=status.HTTP_201_CREATED)
def create_booking(
    payload: BookingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Блокируем строку слота на время транзакции, чтобы два параллельных
    # запроса на один и тот же слот не оба увидели is_booked=False.
    slot = (
        db.query(Slot)
        .filter(Slot.id == payload.slot_id)
        .with_for_update()
        .first()
    )
    if not slot:
        raise HTTPException(status_code=404, detail="Слот не найден")
    if slot.is_booked:
        raise HTTPException(status_code=409, detail="Этот слот уже забронирован")

    slot.is_booked = True
    booking = Booking(user_id=current_user.id, slot_id=slot.id, status=BookingStatus.confirmed)
    db.add(booking)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Этот слот уже забронирован")
    db.refresh(booking)
    return booking


@router.get("/bookings/me", response_model=list[BookingOut])
def my_bookings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Booking).filter(Booking.user_id == current_user.id).order_by(Booking.created_at.desc()).all()


@router.delete("/bookings/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    booking = (
        db.query(Booking)
        .filter(Booking.id == booking_id, Booking.user_id == current_user.id)
        .first()
    )
    if not booking:
        raise HTTPException(status_code=404, detail="Бронь не найдена")
    booking.status = BookingStatus.cancelled
    booking.slot.is_booked = False
    db.commit()
