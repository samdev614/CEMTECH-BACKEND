from sqlalchemy import Column, Integer, String
from app.core.database import Base

class ServiceMedia(Base):
    __tablename__ = "service_media"

    id         = Column(Integer, primary_key=True, index=True)
    key        = Column(String(50), unique=True, index=True, nullable=False)
    media_url  = Column(String, nullable=True)
    media_type = Column(String(10), default="image")  # "image" or "video"
