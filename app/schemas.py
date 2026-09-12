"""Pydantic-схемы запросов/ответов API."""
from datetime import datetime

from pydantic import BaseModel, EmailStr, ConfigDict

from app.models import BookingStatus


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    full_name: str
    is_admin: bool


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ServiceCreate(BaseModel):
    name: str
    duration_minutes: int
    price: float


class ServiceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    duration_minutes: int
    price: float


class SlotOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    service_id: int
    starts_at: datetime
    is_booked: bool


class BookingCreate(BaseModel):
    slot_id: int


class BookingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    slot_id: int
    status: BookingStatus
    created_at: datetime
