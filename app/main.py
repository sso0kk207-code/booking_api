"""Точка входа FastAPI-приложения."""
from fastapi import FastAPI

from app.database import Base, engine
from app.routers import auth, bookings, services

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Booking API",
    description="REST API сервиса бронирования: услуги, слоты, брони, JWT-авторизация.",
    version="1.0.0",
)

app.include_router(auth.router)
app.include_router(services.router)
app.include_router(bookings.router)


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}
