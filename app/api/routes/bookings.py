from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.security import require_admin
from app.models.booking import Booking
from app.schemas.booking import BookingCreate, BookingOut

router = APIRouter()

@router.post("/", response_model=BookingOut)
def create_booking(data: BookingCreate, db: Session = Depends(get_db)):
    booking = Booking(**data.model_dump())
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking

@router.get("/admin/all", response_model=List[BookingOut])
def admin_list_bookings(db: Session = Depends(get_db), _=Depends(require_admin)):
    return db.query(Booking).order_by(Booking.created_at.desc()).all()

@router.patch("/admin/{booking_id}/status")
def update_booking_status(
    booking_id: int,
    status: str,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if status not in ("pending", "confirmed", "cancelled"):
        raise HTTPException(status_code=400, detail="Invalid status")
    booking.status = status
    db.commit()
    return {"message": "Updated", "status": status}

@router.delete("/admin/{booking_id}")
def delete_booking(booking_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    db.delete(booking)
    db.commit()
    return {"message": "Deleted"}
