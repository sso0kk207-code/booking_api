"""Услуги и генерация свободных слотов под них."""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_admin
from app.models import Service, Slot
from app.schemas import ServiceCreate, ServiceOut, SlotOut

router = APIRouter(prefix="/services", tags=["services"])


@router.get("", response_model=list[ServiceOut])
def list_services(db: Session = Depends(get_db)):
    return db.query(Service).all()


@router.post("", response_model=ServiceOut, dependencies=[Depends(get_current_admin)])
def create_service(payload: ServiceCreate, db: Session = Depends(get_db)):
    service = Service(**payload.model_dump())
    db.add(service)
    db.commit()
    db.refresh(service)
    return service


@router.post("/{service_id}/generate-slots", response_model=list[SlotOut], dependencies=[Depends(get_current_admin)])
def generate_slots(service_id: int, date_from: datetime, days: int = 7, db: Session = Depends(get_db)):
    """Утилита для админа: нарезать рабочий день на слоты по длительности услуги."""
    service = db.query(Service).get(service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Услуга не найдена")

    created: list[Slot] = []
    step = timedelta(minutes=service.duration_minutes)
    for day in range(days):
        day_start = date_from.replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=day)
        day_end = date_from.replace(hour=18, minute=0, second=0, microsecond=0) + timedelta(days=day)
        cursor = day_start
        while cursor + step <= day_end:
            exists = (
                db.query(Slot)
                .filter(Slot.service_id == service_id, Slot.starts_at == cursor)
                .first()
            )
            if not exists:
                slot = Slot(service_id=service_id, starts_at=cursor)
                db.add(slot)
                created.append(slot)
            cursor += step
    db.commit()
    for slot in created:
        db.refresh(slot)
    return created
