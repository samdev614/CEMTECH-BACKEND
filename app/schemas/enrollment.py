from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict

class EnrollmentBase(BaseModel):
    user_id: int
    course_id: int
    status: str = "pending"
    payment_status: str = "pending"
    price_paid: Decimal

class EnrollmentCreate(EnrollmentBase):
    pass

class EnrollmentOut(EnrollmentBase):
    id: int
    enrollment_date: datetime

    model_config = ConfigDict(from_attributes=True)

class CourseRatingBase(BaseModel):
    rating: int
    comment: str | None = None

class CourseRatingCreate(CourseRatingBase):
    pass

class CourseRatingOut(CourseRatingBase):
    id: int
    user_id: int
    course_id: int
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

# New schema to check enrollment status and existing rating
class CourseEnrollmentStatus(BaseModel):
    is_enrolled: bool
    can_rate: bool
    purchase_state: str = "none"
    my_rating: CourseRatingOut | None = None

    model_config = ConfigDict(from_attributes=True)
