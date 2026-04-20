import uuid
from pathlib import Path
from fastapi import HTTPException, UploadFile
from app.core.config import settings

ALLOWED_IMAGES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
ALLOWED_FILES  = {"application/zip", "application/pdf", "application/octet-stream",
                  "application/x-zip-compressed"}
MAX_BYTES = settings.MAX_FILE_SIZE_MB * 1024 * 1024

async def save_image(file: UploadFile) -> str:
    if file.content_type not in ALLOWED_IMAGES:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, WebP, GIF allowed")
    data = await file.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=400, detail=f"File too large (max {settings.MAX_FILE_SIZE_MB}MB)")
    ext = file.filename.rsplit(".", 1)[-1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    dest = Path(settings.UPLOAD_DIR) / "images" / filename
    dest.write_bytes(data)
    return f"/uploads/images/{filename}"

async def save_product_file(file: UploadFile) -> str:
    data = await file.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=400, detail=f"File too large (max {settings.MAX_FILE_SIZE_MB}MB)")
    ext = file.filename.rsplit(".", 1)[-1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    dest = Path(settings.UPLOAD_DIR) / "products" / filename
    dest.write_bytes(data)
    return f"/uploads/products/{filename}"
