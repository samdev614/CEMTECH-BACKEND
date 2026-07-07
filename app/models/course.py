from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Course(Base):
    __tablename__ = "courses"

    id           = Column(Integer, primary_key=True, index=True)
    title        = Column(String(300), nullable=False)
    slug         = Column(String(300), unique=True, index=True, nullable=False)
    subtitle     = Column(String(300))
    description  = Column(Text)
    category     = Column(String(100))
    language     = Column(String(50))
    price        = Column(Numeric(10, 2), nullable=False)
    duration     = Column(String(100))
    level        = Column(String(50))
    instructor   = Column(String(200))
    preview_url  = Column(String)
    cover_image  = Column(String)
    what_you_will_learn = Column(Text)
    requirements = Column(Text)
    includes     = Column(Text)
    course_content = Column(Text)
    target_audience = Column(Text)
    is_published = Column(Boolean, default=False)
    is_featured  = Column(Boolean, default=False)
    sort_order   = Column(Integer, default=0)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())
    updated_at   = Column(DateTime(timezone=True), onupdate=func.now())

    enrollments = relationship("Enrollment", back_populates="course")
    course_ratings = relationship("CourseRating", back_populates="course")

    @property
    def enrollment_count(self) -> int:
        return len(self.enrollments)

    @property
    def students_count(self) -> int:
        return len(self.enrollments)

    @property
    def reviews_count(self) -> int:
        return len(self.course_ratings)

    @property
    def average_rating(self) -> float:
        ratings = [r.rating for r in self.course_ratings]
        return sum(ratings) / len(ratings) if ratings else 0.0

    @property
    def rating(self) -> float:
        return self.average_rating
