from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base


class Documentation(Base):
    __tablename__ = "documentation"

    id            = Column(Integer, primary_key=True, index=True)
    title         = Column(String(300), nullable=False)
    slug          = Column(String(300), unique=True, index=True, nullable=False)
    excerpt       = Column(Text)
    content       = Column(Text, nullable=False)
    cover_image   = Column(String)
    category      = Column(String(100))
    sort_order    = Column(Integer, default=0)
    is_published  = Column(Boolean, default=False)
    author_id     = Column(Integer, ForeignKey("users.id"))
    created_at    = Column(DateTime(timezone=True), server_default=func.now())
    updated_at    = Column(DateTime(timezone=True), onupdate=func.now())
    published_at  = Column(DateTime(timezone=True))
