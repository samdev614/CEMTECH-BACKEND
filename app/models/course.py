from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Numeric
from sqlalchemy.sql import func
from app.core.database import Base

class Course(Base):
    __tablename__ = "courses"

    id           = Column(Integer, primary_key=True, index=True)
    title        = Column(String(300), nullable=False)
    slug         = Column(String(300), unique=True, index=True, nullable=False)
    description  = Column(Text)
    category     = Column(String(100))
    price        = Column(Numeric(10, 2), nullable=False)
    duration     = Column(String(100))
    level        = Column(String(50))
    instructor   = Column(String(200))
    preview_url  = Column(String)
    cover_image  = Column(String)
    is_published = Column(Boolean, default=False)
    is_featured  = Column(Boolean, default=False)
    sort_order   = Column(Integer, default=0)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())
    updated_at   = Column(DateTime(timezone=True), onupdate=func.now())
