from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base

class BlogPost(Base):
    __tablename__ = "blog_posts"

    id           = Column(Integer, primary_key=True, index=True)
    title        = Column(String(300), nullable=False)
    slug         = Column(String(300), unique=True, index=True, nullable=False)
    excerpt      = Column(Text)
    content      = Column(Text, nullable=False)
    cover_image  = Column(String)       # path to uploaded image
    category     = Column(String(100))
    tags         = Column(String(500))  # comma-separated
    is_published = Column(Boolean, default=False)
    read_time    = Column(Integer, default=5)  # minutes
    author_id    = Column(Integer, ForeignKey("users.id"))
    created_at   = Column(DateTime(timezone=True), server_default=func.now())
    updated_at   = Column(DateTime(timezone=True), onupdate=func.now())
    published_at = Column(DateTime(timezone=True))
