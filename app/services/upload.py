import uuid
from pathlib import Path
from fastapi import HTTPException, UploadFile
import cloudinary
import cloudinary.uploader
from app.core.config import settings

cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True
)

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

    try:
        upload_result = cloudinary.uploader.upload(data, folder="cemtech/images")
        return upload_result.get("secure_url")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cloudinary upload failed: {str(e)}")

async def save_product_file(file: UploadFile) -> str:
    return await save_file(file, "products")

async def save_file(file: UploadFile, folder: str = "files") -> str:
    data = await file.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=400, detail=f"File too large (max {settings.MAX_FILE_SIZE_MB}MB)")
    ext = file.filename.rsplit(".", 1)[-1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    dest = Path(settings.UPLOAD_DIR) / folder / filename
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return f"/uploads/{folder}/{filename}"
