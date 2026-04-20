from pydantic import BaseModel, EmailStr
from datetime import datetime

class BookingCreate(BaseModel):
    service: str
    full_name: str
    email: EmailStr
    phone: str | None = None
    booked_date: str
    booked_time: str
    notes: str | None = None

class BookingOut(BaseModel):
    id: int
    service: str
    full_name: str
    email: str
    phone: str | None
    booked_date: str
    booked_time: str
    notes: str | None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
