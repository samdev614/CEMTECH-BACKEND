from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime

class CourseOut(BaseModel):
    id: int
    title: str
    slug: str
    description: str | None
    category: str | None
    price: Decimal
    duration: str | None
    level: str | None
    instructor: str | None
    preview_url: str | None
    cover_image: str | None
    is_published: bool
    is_featured: bool
    sort_order: int
    created_at: datetime

    model_config = {"from_attributes": True}
