from fastapi import APIRouter, Depends, Form, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.security import require_admin
from app.models.settings import ServiceMedia
from app.schemas.settings import ServiceMediaOut
from app.services.upload import save_image

router = APIRouter()

VALID_KEYS = {"web_dev", "video_prod", "marketing"}

def _ensure_defaults(db: Session):
    """Seed the three rows if they don't exist yet."""
    for key in VALID_KEYS:
        if not db.query(ServiceMedia).filter(ServiceMedia.key == key).first():
            db.add(ServiceMedia(key=key, media_url=None, media_type="image"))
    db.commit()


@router.get("/services", response_model=List[ServiceMediaOut])
def get_services(db: Session = Depends(get_db)):
    _ensure_defaults(db)
    return db.query(ServiceMedia).all()


@router.patch("/services/{key}", response_model=ServiceMediaOut)
async def update_service(
    key: str,
    media_type: str = Form(...),
    media_url: str = Form(None),
    media_image: UploadFile = File(None),
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    _ensure_defaults(db)
    row = db.query(ServiceMedia).filter(ServiceMedia.key == key).first()
    if not row:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Service key not found")

    row.media_type = media_type

    if media_type == "image" and media_image and media_image.filename:
        row.media_url = await save_image(media_image)
    elif media_type == "video" and media_url:
        row.media_url = media_url

    db.commit()
    db.refresh(row)
    return row
