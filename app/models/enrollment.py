from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    enrollment_date = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String, default="pending") # e.g., "pending", "completed", "active", "cancelled"
    payment_status = Column(String, default="pending") # e.g., "pending", "paid", "failed"
    price_paid = Column(DECIMAL(10, 2), nullable=False)

    user = relationship("User", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")

    # Add a unique constraint to prevent duplicate enrollments
    __table_args__ = (
        UniqueConstraint('user_id', 'course_id', name='_user_course_uc'),
    )

from sqlalchemy import UniqueConstraint