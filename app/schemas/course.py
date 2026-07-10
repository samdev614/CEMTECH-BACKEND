from pydantic import BaseModel, ConfigDict, model_validator # Import model_validator
from decimal import Decimal
from datetime import datetime
from typing import List, Optional
from app.schemas.course_content import CourseSectionOut, CourseSectionCreate, CourseSectionUpdate # Import CourseSectionUpdate

class CourseBase(BaseModel):
    title: str
    slug: str
    subtitle: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    language: Optional[str] = "English"
    price: Decimal
    is_free: bool = False
    duration: Optional[str] = None
    level: Optional[str] = None
    instructor: Optional[str] = None
    preview_url: Optional[str] = None
    what_you_will_learn: Optional[str] = None
    requirements: Optional[str] = None
    includes: Optional[str] = None
    target_audience: Optional[str] = None
    is_published: bool = False
    is_featured: bool = False
    sort_order: int = 0

    @model_validator(mode='after')
    def set_price_for_free_course(self) -> 'CourseBase':
        if self.is_free:
            self.price = Decimal(0)
        return self

class CourseCreate(CourseBase):
    sections: List[CourseSectionCreate] = []

class CourseUpdate(CourseBase):
    # All fields are optional for update
    title: Optional[str] = None
    slug: Optional[str] = None
    price: Optional[Decimal] = None
    is_free: Optional[bool] = None
    sections: Optional[List[CourseSectionUpdate]] = None # Use CourseSectionUpdate for nested sections

    @model_validator(mode='after')
    def set_price_for_free_course_update(self) -> 'CourseUpdate':
        # Only apply if is_free is explicitly set to True in the update payload
        if self.is_free is True:
            self.price = Decimal(0)
        return self

class CourseOut(CourseBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    enrollment_count: int = 0
    students_count: int = 0
    reviews_count: int = 0
    average_rating: float = 0.0
    rating: float = 0.0
    cover_image: Optional[str] = None
    sections: List[CourseSectionOut] = []

    model_config = ConfigDict(from_attributes=True)
