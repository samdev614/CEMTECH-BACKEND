from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime

class CourseOut(BaseModel):
    id: int
    title: str
    slug: str
    subtitle: str | None
    description: str | None
    category: str | None
    language: str | None
    price: Decimal
    duration: str | None
    level: str | None
    instructor: str | None
    preview_url: str | None
    cover_image: str | None
    what_you_will_learn: str | None
    requirements: str | None
    includes: str | None
    course_content: str | None
    target_audience: str | None
    is_published: bool
    is_featured: bool
    sort_order: int
    enrollment_count: int = 0
    students_count: int = 0
    reviews_count: int = 0
    average_rating: float = 0.0
    rating: float = 0.0
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}
