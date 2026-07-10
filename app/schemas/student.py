from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class StudentEnrollmentOut(BaseModel):
    enrollment_id: int
    user_id: int
    student_name: str
    email: str
    course_id: int
    course_title: str
    course_slug: str
    enrollment_date: datetime
    status: str
    payment_status: str
    price_paid: Decimal
    certificate_eligible: bool = False
    certificate_status: str = "Not ready"

    model_config = ConfigDict(from_attributes=True)


class StudentEnrollmentUpdate(BaseModel):
    status: str | None = None
    payment_status: str | None = None


class StudentTrackingSummaryOut(BaseModel):
    total_students: int = 0
    total_enrollments: int = 0
    active_enrollments: int = 0
    completed_enrollments: int = 0
    certificate_ready: int = 0
    pending_payments: int = 0


class StudentTrackingOut(BaseModel):
    summary: StudentTrackingSummaryOut
    students: list[StudentEnrollmentOut]

    model_config = ConfigDict(from_attributes=True)
