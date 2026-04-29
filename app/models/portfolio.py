from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class Project(Base):
    __tablename__ = "projects"

    id           = Column(Integer, primary_key=True, index=True)
    title        = Column(String(300), nullable=False)
    slug         = Column(String(300), unique=True, index=True, nullable=False)
    description  = Column(Text)
    category     = Column(String(100))   # Web Dev, Video, Marketing
    tags         = Column(String(500))   # comma-separated
    cover_image  = Column(String)
    live_url     = Column(String)
    video_url    = Column(String)
    source_url   = Column(String)
    use_case     = Column(Text)
    is_featured  = Column(Boolean, default=False)
    is_published = Column(Boolean, default=True)
    sort_order   = Column(Integer, default=0)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())
    updated_at   = Column(DateTime(timezone=True), onupdate=func.now())
