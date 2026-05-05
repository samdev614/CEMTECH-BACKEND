from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from decimal import Decimal
from typing import List
from app.core.database import get_db
from app.core.security import require_admin
from app.models.course import Course
from app.schemas.course import CourseOut
from app.services.upload import save_image

router = APIRouter()


@router.get("/", response_model=List[CourseOut])
def list_courses(db: Session = Depends(get_db), category: str = None):
    q = db.query(Course).filter(Course.is_published == True)
    if category:
        q = q.filter(Course.category == category)
    return q.order_by(Course.sort_order.asc(), Course.created_at.desc()).all()


@router.get("/{slug}", response_model=CourseOut)
def get_course(slug: str, db: Session = Depends(get_db)):
    item = db.query(Course).filter(Course.slug == slug, Course.is_published == True).first()
    if not item:
        raise HTTPException(status_code=404, detail="Course not found")
    return item


@router.get("/admin/all", response_model=List[CourseOut])
def admin_list_courses(db: Session = Depends(get_db), _=Depends(require_admin)):
    return db.query(Course).order_by(Course.sort_order.asc()).all()


@router.post("/admin/", response_model=CourseOut)
async def create_course(
    title: str = Form(...),
    slug: str = Form(...),
    description: str = Form(None),
    category: str = Form(None),
    price: Decimal = Form(...),
    duration: str = Form(None),
    level: str = Form(None),
    instructor: str = Form(None),
    preview_url: str = Form(None),
    is_published: bool = Form(False),
    is_featured: bool = Form(False),
    sort_order: int = Form(0),
    cover_image: UploadFile = File(None),
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    if db.query(Course).filter(Course.slug == slug).first():
        raise HTTPException(status_code=400, detail="Slug already exists")

    image_path = await save_image(cover_image) if cover_image and cover_image.filename else None

    item = Course(
        title=title, slug=slug, description=description, category=category,
        price=price, duration=duration, level=level, instructor=instructor,
        preview_url=preview_url, is_published=is_published, is_featured=is_featured,
        sort_order=sort_order, cover_image=image_path,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/admin/{item_id}", response_model=CourseOut)
async def update_course(
    item_id: int,
    title: str = Form(None),
    slug: str = Form(None),
    description: str = Form(None),
    category: str = Form(None),
    price: Decimal = Form(None),
    duration: str = Form(None),
    level: str = Form(None),
    instructor: str = Form(None),
    preview_url: str = Form(None),
    is_published: bool = Form(None),
    is_featured: bool = Form(None),
    sort_order: int = Form(None),
    cover_image: UploadFile = File(None),
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    item = db.query(Course).filter(Course.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Course not found")

    for field, value in dict(
        title=title, slug=slug, description=description, category=category,
        price=price, duration=duration, level=level, instructor=instructor,
        preview_url=preview_url, is_published=is_published, is_featured=is_featured,
        sort_order=sort_order,
    ).items():
        if value is not None:
            setattr(item, field, value)

    if cover_image and cover_image.filename:
        item.cover_image = await save_image(cover_image)

    db.commit()
    db.refresh(item)
    return item


@router.delete("/admin/{item_id}")
def delete_course(item_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    item = db.query(Course).filter(Course.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Course not found")
    db.delete(item)
    db.commit()
    return {"message": "Deleted"}
