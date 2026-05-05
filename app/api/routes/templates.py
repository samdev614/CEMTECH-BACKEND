from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from decimal import Decimal
from typing import List
from app.core.database import get_db
from app.core.security import require_admin
from app.models.template import Template
from app.schemas.template import TemplateOut
from app.services.upload import save_image, save_file

router = APIRouter()


@router.get("/", response_model=List[TemplateOut])
def list_templates(db: Session = Depends(get_db), category: str = None):
    q = db.query(Template).filter(Template.is_published == True)
    if category:
        q = q.filter(Template.category == category)
    return q.order_by(Template.sort_order.asc(), Template.created_at.desc()).all()


@router.get("/{slug}", response_model=TemplateOut)
def get_template(slug: str, db: Session = Depends(get_db)):
    item = db.query(Template).filter(Template.slug == slug, Template.is_published == True).first()
    if not item:
        raise HTTPException(status_code=404, detail="Template not found")
    return item


@router.get("/admin/all", response_model=List[TemplateOut])
def admin_list_templates(db: Session = Depends(get_db), _=Depends(require_admin)):
    return db.query(Template).order_by(Template.sort_order.asc()).all()


@router.post("/admin/", response_model=TemplateOut)
async def create_template(
    name: str = Form(...),
    slug: str = Form(...),
    description: str = Form(None),
    category: str = Form(None),
    price: Decimal = Form(...),
    is_published: bool = Form(False),
    is_featured: bool = Form(False),
    sort_order: int = Form(0),
    cover_image: UploadFile = File(None),
    template_file: UploadFile = File(None),
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    if db.query(Template).filter(Template.slug == slug).first():
        raise HTTPException(status_code=400, detail="Slug already exists")

    image_path = await save_image(cover_image) if cover_image and cover_image.filename else None
    file_path  = await save_file(template_file, "templates") if template_file and template_file.filename else None

    item = Template(
        name=name, slug=slug, description=description, category=category,
        price=price, is_published=is_published, is_featured=is_featured,
        sort_order=sort_order, cover_image=image_path, file_path=file_path,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/admin/{item_id}", response_model=TemplateOut)
async def update_template(
    item_id: int,
    name: str = Form(None),
    slug: str = Form(None),
    description: str = Form(None),
    category: str = Form(None),
    price: Decimal = Form(None),
    is_published: bool = Form(None),
    is_featured: bool = Form(None),
    sort_order: int = Form(None),
    cover_image: UploadFile = File(None),
    template_file: UploadFile = File(None),
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    item = db.query(Template).filter(Template.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Template not found")

    for field, value in dict(
        name=name, slug=slug, description=description, category=category,
        price=price, is_published=is_published, is_featured=is_featured, sort_order=sort_order,
    ).items():
        if value is not None:
            setattr(item, field, value)

    if cover_image and cover_image.filename:
        item.cover_image = await save_image(cover_image)
    if template_file and template_file.filename:
        item.file_path = await save_file(template_file, "templates")

    db.commit()
    db.refresh(item)
    return item


@router.delete("/admin/{item_id}")
def delete_template(item_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    item = db.query(Template).filter(Template.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Template not found")
    db.delete(item)
    db.commit()
    return {"message": "Deleted"}
