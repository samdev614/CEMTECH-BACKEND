from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.core.security import require_admin
from app.models.enrollment import Enrollment
from app.schemas.student import (
    StudentEnrollmentOut,
    StudentEnrollmentUpdate,
    StudentTrackingOut,
    StudentTrackingSummaryOut,
)

router = APIRouter()


def _certificate_status(enrollment: Enrollment) -> str:
    if enrollment.payment_status != "paid":
        return "Payment pending"
    if enrollment.status == "completed":
        return "Ready to issue"
    if enrollment.status == "active":
        return "In progress"
    return enrollment.status.replace("_", " ").title()


def _serialize_enrollment(enrollment: Enrollment) -> StudentEnrollmentOut:
    user = enrollment.user
    course = enrollment.course
    if not user or not course:
        raise ValueError("Enrollment is missing linked user or course")

    return StudentEnrollmentOut(
        enrollment_id=enrollment.id,
        user_id=user.id,
        student_name=user.full_name or user.email,
        email=user.email,
        course_id=course.id,
        course_title=course.title,
        course_slug=course.slug,
        enrollment_date=enrollment.enrollment_date,
        status=enrollment.status,
        payment_status=enrollment.payment_status,
        price_paid=enrollment.price_paid or 0,
        certificate_eligible=enrollment.payment_status == "paid" and enrollment.status == "completed",
        certificate_status=_certificate_status(enrollment),
    )


@router.get("/students", response_model=StudentTrackingOut)
def list_students(db: Session = Depends(get_db), _=Depends(require_admin)):
    enrollments = (
        db.query(Enrollment)
        .options(
            selectinload(Enrollment.user),
            selectinload(Enrollment.course),
        )
        .order_by(Enrollment.enrollment_date.desc())
        .all()
    )

    rows = []
    unique_student_ids = set()
    active_enrollments = 0
    completed_enrollments = 0
    certificate_ready = 0
    pending_payments = 0

    for enrollment in enrollments:
        if not enrollment.user or not enrollment.course:
            continue

        unique_student_ids.add(enrollment.user.id)
        if enrollment.status == "active":
            active_enrollments += 1
        if enrollment.status == "completed":
            completed_enrollments += 1
        if enrollment.payment_status != "paid":
            pending_payments += 1

        serialized = _serialize_enrollment(enrollment)
        if serialized.certificate_eligible:
            certificate_ready += 1
        rows.append(serialized)

    summary = StudentTrackingSummaryOut(
        total_students=len(unique_student_ids),
        total_enrollments=len(rows),
        active_enrollments=active_enrollments,
        completed_enrollments=completed_enrollments,
        certificate_ready=certificate_ready,
        pending_payments=pending_payments,
    )

    return StudentTrackingOut(summary=summary, students=rows)


@router.patch("/students/{enrollment_id}", response_model=StudentEnrollmentOut)
def update_student_enrollment(
    enrollment_id: int,
    payload: StudentEnrollmentUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    enrollment = (
        db.query(Enrollment)
        .options(
            selectinload(Enrollment.user),
            selectinload(Enrollment.course),
        )
        .filter(Enrollment.id == enrollment_id)
        .first()
    )
    if not enrollment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enrollment not found")

    if payload.status is not None:
        enrollment.status = payload.status
    if payload.payment_status is not None:
        enrollment.payment_status = payload.payment_status

    db.commit()
    db.refresh(enrollment)
    return _serialize_enrollment(enrollment)
