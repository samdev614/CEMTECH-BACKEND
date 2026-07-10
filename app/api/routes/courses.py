import json
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Body
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import or_
from decimal import Decimal
from typing import List, Optional
from app.core.database import get_db
from app.core.security import require_admin, get_current_user, get_optional_current_user
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.rating import CourseRating
from app.models.course_content import CourseSection, CourseLesson
from app.models.product import Order
from app.schemas.course import CourseOut, CourseCreate, CourseUpdate
from app.schemas.enrollment import CourseRatingOut, CourseRatingCreate, CourseEnrollmentStatus
from app.services.upload import save_image, save_video
from app.models.user import User # Import User model

router = APIRouter()


def _clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


# Helper to check if a URL is a YouTube embed URL
def is_youtube_url(url: Optional[str]) -> bool:
    if not url:
        return False
    # Check for common YouTube URL patterns
    return "youtube.com/watch?v=" in url or "youtu.be/" in url or "youtube.com/embed/" in url


def _latest_course_order(db: Session, user: User, course_id: int) -> Order | None:
    return (
        db.query(Order)
        .filter(
            Order.course_id == course_id,
            Order.item_type == "course",
            or_(Order.user_id == user.id, Order.customer_email == user.email),
        )
        .order_by(Order.created_at.desc())
        .first()
    )


def _sync_paid_course_enrollment(db: Session, user: User, course: Course) -> bool:
    enrollment = db.query(Enrollment).filter(
        Enrollment.user_id == user.id,
        Enrollment.course_id == course.id,
        Enrollment.status == "active",
    ).first()
    if enrollment:
        return True

    paid_order = (
        db.query(Order)
        .filter(
            Order.course_id == course.id,
            Order.item_type == "course",
            Order.status == "paid",
            or_(Order.user_id == user.id, Order.customer_email == user.email),
        )
        .order_by(Order.created_at.desc())
        .first()
    )
    if not paid_order:
        return False

    enrollment = db.query(Enrollment).filter(
        Enrollment.user_id == user.id,
        Enrollment.course_id == course.id,
    ).first()

    if not enrollment:
        enrollment = Enrollment(
            user_id=user.id,
            course_id=course.id,
            status="active",
            payment_status="paid",
            price_paid=paid_order.amount,
        )
        db.add(enrollment)
    else:
        enrollment.status = "active"
        enrollment.payment_status = "paid"
        if enrollment.price_paid is None or Decimal(enrollment.price_paid) <= 0:
            enrollment.price_paid = paid_order.amount

    db.commit()
    db.refresh(enrollment)
    return True


def _course_purchase_state(db: Session, user: User, course: Course) -> str:
    if _sync_paid_course_enrollment(db, user, course):
        return "active"

    latest_pending_order = (
        db.query(Order)
        .filter(
            Order.course_id == course.id,
            Order.item_type == "course",
            Order.status == "pending",
            or_(Order.user_id == user.id, Order.customer_email == user.email),
        )
        .order_by(Order.created_at.desc())
        .first()
    )
    if latest_pending_order:
        return "pending"

    return "none"


def _sync_paid_course_enrollments(db: Session, user: User) -> None:
    paid_course_ids = (
        db.query(Order.course_id)
        .filter(
            Order.item_type == "course",
            Order.status == "paid",
            or_(Order.user_id == user.id, Order.customer_email == user.email),
        )
        .distinct()
        .all()
    )

    for (course_id,) in paid_course_ids:
        course = db.query(Course).filter(Course.id == course_id, Course.is_published == True).first()
        if course:
            _sync_paid_course_enrollment(db, user, course)


@router.get("/", response_model=List[CourseOut])
def list_courses(db: Session = Depends(get_db), category: str = None):
    q = (
        db.query(Course)
        .options(
            selectinload(Course.enrollments),
            selectinload(Course.course_ratings),
            selectinload(Course.sections).selectinload(CourseSection.lessons)
        )
        .filter(Course.is_published == True)
    )
    if category:
        q = q.filter(Course.category == category)
    return q.order_by(Course.sort_order.asc(), Course.created_at.desc()).all()


@router.get("/{slug}", response_model=CourseOut)
def get_course(slug: str, db: Session = Depends(get_db), current_user: Optional[User] = Depends(get_optional_current_user)):
    item = (
        db.query(Course)
        .options(
            selectinload(Course.enrollments),
            selectinload(Course.course_ratings),
            selectinload(Course.sections).selectinload(CourseSection.lessons)
        )
        .filter(Course.slug == slug, Course.is_published == True)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Course not found")

    # Check if user is enrolled
    purchase_state = "none"
    if current_user:
        purchase_state = _course_purchase_state(db, current_user, item)

    is_enrolled = purchase_state == "active"

    # Conditional video_url modification for paid courses if user is not enrolled
    if not item.is_free and not is_enrolled:
        for section in item.sections:
            for i, lesson in enumerate(section.lessons):
                if i >= 2:  # Only allow first two lessons for non-enrolled users in paid courses
                    lesson.video_url = None

    return item


@router.get("/me/enrolled", response_model=List[CourseOut])
def list_my_enrolled_courses(
    db: Session = Depends(get_db), 
    current_user = Depends(get_current_user)
):
    """List all courses the current user has successfully enrolled in."""
    _sync_paid_course_enrollments(db, current_user)

    enrolled_ids = db.query(Enrollment.course_id).filter(
        Enrollment.user_id == current_user.id,
        Enrollment.status == "active"
    ).all()
    
    # Extract IDs from list of tuples
    ids = [r[0] for r in enrolled_ids]
    
    return (
        db.query(Course)
        .options(
            selectinload(Course.enrollments),
            selectinload(Course.course_ratings),
            selectinload(Course.sections).selectinload(CourseSection.lessons)
        )
        .filter(Course.id.in_(ids))
        .all()
    )


@router.get("/{slug}/related", response_model=List[CourseOut])
def get_related_courses(slug: str, db: Session = Depends(get_db)):
    course = (
        db.query(Course)
        .options(
            selectinload(Course.enrollments),
            selectinload(Course.course_ratings),
            selectinload(Course.sections).selectinload(CourseSection.lessons)
        )
        .filter(Course.slug == slug)
        .first()
    )
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    return (
        db.query(Course)
        .options(
            selectinload(Course.enrollments),
            selectinload(Course.course_ratings),
            selectinload(Course.sections).selectinload(CourseSection.lessons)
        )
        .filter(
            Course.category == course.category,
            Course.slug != slug,
            Course.is_published == True
        )
        .order_by(Course.is_featured.desc(), Course.sort_order.asc(), Course.created_at.desc())
        .limit(3)
        .all()
    )


@router.get("/{slug}/enrollment-status", response_model=CourseEnrollmentStatus)
def get_course_enrollment_status(
    slug: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user) # User must be logged in
):
    """
    Checks if the current user is enrolled in a course and if they have rated it.
    """
    course = db.query(Course).filter(Course.slug == slug, Course.is_published == True).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found or not published")

    purchase_state = _course_purchase_state(db, current_user, course)
    is_enrolled = purchase_state == "active"

    my_rating = None
    if is_enrolled:
        my_rating = db.query(CourseRating).filter(
            CourseRating.user_id == current_user.id,
            CourseRating.course_id == course.id
        ).first()

    return CourseEnrollmentStatus(
        is_enrolled=is_enrolled,
        can_rate=is_enrolled, # User can rate if enrolled
        purchase_state=purchase_state,
        my_rating=my_rating
    )


@router.post("/{slug}/rate", response_model=CourseRatingOut)
def rate_course(
    slug: str, 
    data: CourseRatingCreate, 
    db: Session = Depends(get_db), 
    current_user = Depends(get_current_user)
):
    """Allow enrolled students to submit or update a rating for a course."""
    course = db.query(Course).filter(Course.slug == slug).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Ensure user is actually enrolled
    enrolled = db.query(Enrollment).filter(
        Enrollment.user_id == current_user.id,
        Enrollment.course_id == course.id,
        Enrollment.status == "active"
    ).first()
    
    if not enrolled:
        raise HTTPException(status_code=403, detail="You must be enrolled to rate this course")

    # Check if a rating already exists to update it, otherwise create new
    rating = db.query(CourseRating).filter(
        CourseRating.user_id == current_user.id,
        CourseRating.course_id == course.id
    ).first()

    if rating:
        rating.rating = data.rating
        rating.comment = data.comment
    else:
        rating = CourseRating(
            user_id=current_user.id,
            course_id=course.id,
            rating=data.rating,
            comment=data.comment
        )
        db.add(rating)

    db.commit()
    db.refresh(rating)
    return rating


@router.post("/{slug}/checkout", status_code=status.HTTP_201_CREATED)
def checkout_course(
    slug: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Allows an authenticated user to 'checkout' (enroll in) a course.
    """
    course = db.query(Course).filter(Course.slug == slug, Course.is_published == True).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found or not published")

    # Check if user is already enrolled
    existing_enrollment = db.query(Enrollment).filter(
        Enrollment.user_id == current_user.id,
        Enrollment.course_id == course.id
    ).first()

    if existing_enrollment:
        if existing_enrollment.status == "active":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You are already enrolled in this course")
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"An enrollment for this course already exists with status: {existing_enrollment.status}")

    # If course is free, create enrollment directly
    if course.price == 0 or course.is_free:
        new_enrollment = Enrollment(
            user_id=current_user.id,
            course_id=course.id,
            status="active",
            payment_status="paid", # Mark as paid even if free
            price_paid=Decimal(0)
        )
        db.add(new_enrollment)
        db.commit()
        db.refresh(new_enrollment)
        return {"message": "Successfully enrolled in the free course", "enrollment_id": new_enrollment.id}


    # For paid courses, proceed with payment (Mpesa integration would be here)
    # For now, this part is a placeholder for actual payment processing
    new_enrollment = Enrollment(
        user_id=current_user.id,
        course_id=course.id,
        status="pending", # Status is pending until payment is confirmed
        payment_status="pending",
        price_paid=course.price
    )

    db.add(new_enrollment)
    db.commit()
    db.refresh(new_enrollment)

    # This is where Mpesa STK push would be initiated for paid courses
    # For now, we'll just return the pending enrollment
    return {"message": "Enrollment initiated, awaiting payment", "enrollment_id": new_enrollment.id}


@router.get("/admin/all", response_model=List[CourseOut])
def admin_list_courses(db: Session = Depends(get_db), _=Depends(require_admin)):
    return (
        db.query(Course)
        .options(
            selectinload(Course.enrollments),
            selectinload(Course.course_ratings),
            selectinload(Course.sections).selectinload(CourseSection.lessons)
        )
        .order_by(Course.sort_order.asc(), Course.created_at.desc())
        .all()
    )


@router.post("/admin/", response_model=CourseOut)
async def create_course(
    course_data: str = Form(...),
    cover_image: Optional[UploadFile] = File(None),
    preview_video: Optional[UploadFile] = File(None), # New parameter for preview video
    video_files: List[UploadFile] = File([]),
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    try:
        parsed_course_data = CourseCreate.model_validate_json(course_data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format for course_data")
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Validation error for course_data: {e}")

    if db.query(Course).filter(Course.slug == parsed_course_data.slug).first():
        raise HTTPException(status_code=400, detail="Slug already exists")

    image_path = await save_image(cover_image) if cover_image and cover_image.filename else None
    
    preview_video_url = None
    if preview_video and preview_video.filename:
        preview_video_url = await save_video(preview_video)
    elif parsed_course_data.preview_url and not is_youtube_url(parsed_course_data.preview_url):
        preview_video_url = parsed_course_data.preview_url


    item = Course(
        **parsed_course_data.model_dump(exclude_unset=True, exclude={'sections', 'preview_url'}),
        cover_image=image_path,
        preview_url=preview_video_url, # Set the determined preview URL
        course_content=None
    )
    db.add(item)
    db.flush()

    for section_data in parsed_course_data.sections:
        section = CourseSection(
            course_id=item.id,
            **section_data.model_dump(exclude_unset=True, exclude={'lessons'})
        )
        db.add(section)
        db.flush()

        for lesson_data in section_data.lessons:
            video_url_to_save = None # Default to None
            if lesson_data.uploaded_video_index is not None:
                # New video file uploaded, save it
                try:
                    uploaded_file = video_files[lesson_data.uploaded_video_index]
                    video_url_to_save = await save_video(uploaded_file)
                except IndexError:
                    raise HTTPException(status_code=400, detail=f"Video file not found for index {lesson_data.uploaded_video_index}")
                except Exception as e:
                    raise HTTPException(status_code=500, detail=f"Failed to upload video for lesson: {e}")
            elif lesson_data.video_url and not is_youtube_url(lesson_data.video_url):
                # No new file, but existing URL is not YouTube, so keep it
                video_url_to_save = lesson_data.video_url
            # If no new file and it's a YouTube URL, video_url_to_save remains None

            lesson = CourseLesson(
                section_id=section.id,
                video_url=video_url_to_save, # Use the determined video URL
                **lesson_data.model_dump(exclude_unset=True, exclude={'uploaded_video_index', 'video_url'})
            )
            db.add(lesson)

    db.commit()
    db.refresh(item)
    return item


@router.patch("/admin/{item_id}", response_model=CourseOut)
async def update_course(
    item_id: int,
    course_data: str = Form(...),
    cover_image: Optional[UploadFile] = File(None),
    preview_video: Optional[UploadFile] = File(None), # New parameter for preview video
    video_files: List[UploadFile] = File([]),
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    try:
        parsed_course_data = CourseUpdate.model_validate_json(course_data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format for course_data")
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Validation error for course_data: {e}")

    item = db.query(Course).filter(Course.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Course not found")

    # Update main Course fields
    update_data = parsed_course_data.model_dump(exclude_unset=True, exclude={'sections', 'preview_url'})
    for field, value in update_data.items():
        setattr(item, field, value)
    
    if cover_image and cover_image.filename:
        item.cover_image = await save_image(cover_image)

    # Handle preview video
    if preview_video and preview_video.filename:
        item.preview_url = await save_video(preview_video)
    elif parsed_course_data.preview_url is not None and is_youtube_url(parsed_course_data.preview_url):
        # If no new video uploaded, but existing URL is YouTube, clear it
        item.preview_url = None
    elif parsed_course_data.preview_url is not None:
        # If no new video uploaded, and existing URL is not YouTube, keep it
        item.preview_url = parsed_course_data.preview_url
    # If parsed_course_data.preview_url is None, it means the frontend cleared it or it was never set, so item.preview_url remains None or its existing value if not explicitly cleared.


    # Handle sections and lessons
    if parsed_course_data.sections is not None:
        existing_sections_map = {s.id: s for s in item.sections}
        updated_section_ids = set()

        for section_data in parsed_course_data.sections:
            section_id_for_lookup = section_data.id if isinstance(section_data.id, int) else None

            if section_id_for_lookup and section_id_for_lookup in existing_sections_map:
                # Update existing section
                section = existing_sections_map[section_id_for_lookup]
                section_update_data = section_data.model_dump(exclude_unset=True, exclude={'lessons'})
                for field, value in section_update_data.items():
                    setattr(section, field, value)
                updated_section_ids.add(section.id)

                # Handle lessons within this section
                existing_lessons_map = {l.id: l for l in section.lessons}
                updated_lesson_ids = set()

                for lesson_data in section_data.lessons:
                    lesson_id_for_lookup = lesson_data.id if isinstance(lesson_data.id, int) else None
                    
                    video_url_to_save = None
                    if lesson_data.uploaded_video_index is not None:
                        try:
                            uploaded_file = video_files[lesson_data.uploaded_video_index]
                            video_url_to_save = await save_video(uploaded_file)
                        except IndexError:
                            raise HTTPException(status_code=400, detail=f"Video file not found for index {lesson_data.uploaded_video_index}")
                        except Exception as e:
                            raise HTTPException(status_code=500, detail=f"Failed to upload video for lesson: {e}")
                    elif lesson_data.video_url and not is_youtube_url(lesson_data.video_url):
                        video_url_to_save = lesson_data.video_url
                    # If no new file and it's a YouTube URL, video_url_to_save remains None

                    if lesson_id_for_lookup and lesson_id_for_lookup in existing_lessons_map:
                        # Update existing lesson
                        lesson = existing_lessons_map[lesson_id_for_lookup]
                        lesson_update_data = lesson_data.model_dump(exclude_unset=True, exclude={'uploaded_video_index', 'video_url'})
                        for field, value in lesson_update_data.items():
                            setattr(lesson, field, value)
                        lesson.video_url = video_url_to_save # Update video_url
                        updated_lesson_ids.add(lesson.id)
                    else:
                        # Create new lesson
                        lesson = CourseLesson(
                            section_id=section.id,
                            video_url=video_url_to_save,
                            **lesson_data.model_dump(exclude_unset=True, exclude={'uploaded_video_index', 'video_url'})
                        )
                        db.add(lesson)
                
                # Delete lessons not in the update request
                for lesson_id, lesson_obj in existing_lessons_map.items():
                    if lesson_id not in updated_lesson_ids:
                        db.delete(lesson_obj)
            else:
                # Create new section
                section = CourseSection(
                    course_id=item.id,
                    **section_data.model_dump(exclude_unset=True, exclude={'lessons'})
                )
                db.add(section)
                db.flush()

                for lesson_data in section_data.lessons:
                    video_url_to_save = None
                    if lesson_data.uploaded_video_index is not None:
                        try:
                            uploaded_file = video_files[lesson_data.uploaded_video_index]
                            video_url_to_save = await save_video(uploaded_file)
                        except IndexError:
                            raise HTTPException(status_code=400, detail=f"Video file not found for index {lesson_data.uploaded_video_index}")
                        except Exception as e:
                            raise HTTPException(status_code=500, detail=f"Failed to upload video for lesson: {e}")
                    elif lesson_data.video_url and not is_youtube_url(lesson_data.video_url):
                        video_url_to_save = lesson_data.video_url

                    lesson = CourseLesson(
                        section_id=section.id,
                        video_url=video_url_to_save,
                        **lesson_data.model_dump(exclude_unset=True, exclude={'uploaded_video_index', 'video_url'})
                    )
                    db.add(lesson)
        
        # Delete sections not in the update request
        for section_id, section_obj in existing_sections_map.items():
            if section_id not in updated_section_ids:
                db.delete(section_obj)

    db.commit()
    db.refresh(item)
    return item


@router.delete("/admin/{item_id}")
def delete_course(item_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    item = db.query(Course) \
        .options(selectinload(Course.enrollments), selectinload(Course.course_ratings), selectinload(Course.sections)) \
        .filter(Course.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # SQLAlchemy with cascade="all, delete-orphan" on relationships should handle children
    db.delete(item)
    db.commit()
    return {"message": "Deleted"}
