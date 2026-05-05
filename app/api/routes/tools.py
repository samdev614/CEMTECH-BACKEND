from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.security import require_admin
from app.models.tool import Tool
from app.schemas.tool import ToolOut
from app.services.upload import save_image

router = APIRouter()


@router.get("/", response_model=List[ToolOut])
def list_tools(db: Session = Depends(get_db), category: str = None):
    q = db.query(Tool).filter(Tool.is_published == True)
    if category:
        q = q.filter(Tool.category == category)
    return q.order_by(Tool.sort_order.asc(), Tool.created_at.desc()).all()


@router.get("/{slug}", response_model=ToolOut)
def get_tool(slug: str, db: Session = Depends(get_db)):
    item = db.query(Tool).filter(Tool.slug == slug, Tool.is_published == True).first()
    if not item:
        raise HTTPException(status_code=404, detail="Tool not found")
    return item


@router.get("/admin/all", response_model=List[ToolOut])
def admin_list_tools(db: Session = Depends(get_db), _=Depends(require_admin)):
    return db.query(Tool).order_by(Tool.sort_order.asc()).all()


@router.post("/admin/", response_model=ToolOut)
async def create_tool(
    name: str = Form(...),
    slug: str = Form(...),
    description: str = Form(None),
    category: str = Form(None),
    external_url: str = Form(None),
    is_published: bool = Form(False),
    is_featured: bool = Form(False),
    sort_order: int = Form(0),
    cover_image: UploadFile = File(None),
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    if db.query(Tool).filter(Tool.slug == slug).first():
        raise HTTPException(status_code=400, detail="Slug already exists")

    image_path = await save_image(cover_image) if cover_image and cover_image.filename else None

    item = Tool(
        name=name, slug=slug, description=description, category=category,
        external_url=external_url, is_published=is_published, is_featured=is_featured,
        sort_order=sort_order, cover_image=image_path,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/admin/{item_id}", response_model=ToolOut)
async def update_tool(
    item_id: int,
    name: str = Form(None),
    slug: str = Form(None),
    description: str = Form(None),
    category: str = Form(None),
    external_url: str = Form(None),
    is_published: bool = Form(None),
    is_featured: bool = Form(None),
    sort_order: int = Form(None),
    cover_image: UploadFile = File(None),
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    item = db.query(Tool).filter(Tool.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Tool not found")

    for field, value in dict(
        name=name, slug=slug, description=description, category=category,
        external_url=external_url, is_published=is_published, is_featured=is_featured,
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
def delete_tool(item_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    item = db.query(Tool).filter(Tool.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Tool not found")
    db.delete(item)
    db.commit()
    return {"message": "Deleted"}
