from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_admin
from app.models.gallery import GalleryItem
from app.schemas.gallery import GalleryItemOut
from app.services.upload import save_image

router = APIRouter()


@router.get("/", response_model=list[GalleryItemOut])
def list_gallery_items(db: Session = Depends(get_db)):
    return (
        db.query(GalleryItem)
        .filter(GalleryItem.is_published == True)
        .order_by(GalleryItem.sort_order.asc(), GalleryItem.created_at.desc())
        .all()
    )


@router.get("/admin/all", response_model=list[GalleryItemOut])
def admin_list_gallery_items(db: Session = Depends(get_db), _=Depends(require_admin)):
    return (
        db.query(GalleryItem)
        .order_by(GalleryItem.sort_order.asc(), GalleryItem.created_at.desc())
        .all()
    )


@router.post("/admin/", response_model=GalleryItemOut)
async def create_gallery_item(
    title: str = Form(...),
    category: str = Form(None),
    alt_text: str = Form(None),
    is_published: bool = Form(True),
    sort_order: int = Form(0),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    if not image or not image.filename:
        raise HTTPException(status_code=400, detail="Image is required")

    image_url = await save_image(image)
    item = GalleryItem(
        title=title,
        category=category,
        alt_text=alt_text,
        image_url=image_url,
        is_published=is_published,
        sort_order=sort_order,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/admin/{item_id}", response_model=GalleryItemOut)
async def update_gallery_item(
    item_id: int,
    title: str = Form(None),
    category: str = Form(None),
    alt_text: str = Form(None),
    is_published: bool = Form(None),
    sort_order: int = Form(None),
    image: UploadFile = File(None),
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    item = db.query(GalleryItem).filter(GalleryItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Gallery item not found")

    for field, value in dict(
        title=title,
        category=category,
        alt_text=alt_text,
        is_published=is_published,
        sort_order=sort_order,
    ).items():
        if value is not None:
            setattr(item, field, value)

    if image and image.filename:
        item.image_url = await save_image(image)

    db.commit()
    db.refresh(item)
    return item


@router.delete("/admin/{item_id}")
def delete_gallery_item(
    item_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    item = db.query(GalleryItem).filter(GalleryItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Gallery item not found")

    db.delete(item)
    db.commit()
    return {"message": "Deleted"}
