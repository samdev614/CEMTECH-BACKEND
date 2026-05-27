from fastapi import APIRouter, Depends, Form, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.security import require_admin
from app.models.settings import ServiceMedia
from app.schemas.settings import ServiceMediaOut
from app.services.upload import save_image

router = APIRouter()


@router.get("/services", response_model=List[ServiceMediaOut])
def get_services(db: Session = Depends(get_db)):
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
    row = db.query(ServiceMedia).filter(ServiceMedia.key == key).first()
    if not row:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Service key not found")

    row.media_type = media_type

    # Handle image uploads
    if media_type == "image":
        if media_image and media_image.filename:
            try:
                row.media_url = await save_image(media_image)
            except Exception as e:
                from fastapi import HTTPException
                raise HTTPException(status_code=400, detail=f"Image upload failed: {str(e)}")
        elif media_url:  # Allow setting image URL directly
            row.media_url = media_url
    # Handle video URLs
    elif media_type == "video":
        if media_url:
            row.media_url = media_url
        else:
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="Video requires a media_url")

    db.commit()
    db.refresh(row)
    return row
