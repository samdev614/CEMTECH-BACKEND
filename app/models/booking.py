from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.sql import func
from app.core.database import Base

class Booking(Base):
    __tablename__ = "bookings"

    id           = Column(Integer, primary_key=True, index=True)
    service      = Column(String(100), nullable=False)
    full_name    = Column(String(200), nullable=False)
    email        = Column(String(200), nullable=False)
    phone        = Column(String(50))
    booked_date  = Column(String(50))   # e.g. "Mon Apr 21 2026"
    booked_time  = Column(String(20))   # e.g. "10:00 AM"
    notes        = Column(Text)
    status       = Column(String(50), default="pending")  # pending, confirmed, cancelled
    created_at   = Column(DateTime(timezone=True), server_default=func.now())
