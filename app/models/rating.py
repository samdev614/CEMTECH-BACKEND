from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class CourseRating(Base):
    __tablename__ = "course_ratings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    rating = Column(Integer, nullable=False) # e.g., 1 to 5 stars
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="course_ratings")
    course = relationship("Course", back_populates="course_ratings")

    # Add a unique constraint to prevent a user from rating the same course multiple times
    __table_args__ = (
        UniqueConstraint('user_id', 'course_id', name='_user_course_rating_uc'),
    )

from sqlalchemy import UniqueConstraint