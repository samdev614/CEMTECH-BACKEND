import logging
import mimetypes
import uuid
from pathlib import Path
from fastapi import HTTPException, UploadFile, status
import cloudinary
import cloudinary.uploader
from app.core.config import settings

logger = logging.getLogger(__name__)

cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True
)

BACKEND_ROOT = Path(__file__).resolve().parents[2]
UPLOAD_ROOT = Path(settings.UPLOAD_DIR)
if not UPLOAD_ROOT.is_absolute():
    UPLOAD_ROOT = BACKEND_ROOT / UPLOAD_ROOT

ALLOWED_IMAGES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
ALLOWED_VIDEOS = {"video/mp4", "video/webm", "video/ogg", "video/quicktime"}
ALLOWED_FILES  = {"application/zip", "application/pdf", "application/octet-stream",
                  "application/x-zip-compressed"}
MAX_BYTES = settings.MAX_FILE_SIZE_MB * 1024 * 1024


def _local_upload_path(data: bytes, filename: str | None, folder: str, content_type: str | None = None) -> str:
    original_name = Path(filename or "").name
    suffix = Path(original_name).suffix.lower()
    if not suffix and content_type:
        suffix = mimetypes.guess_extension(content_type) or ""
    if not suffix:
        suffix = ".bin"

    stored_name = f"{uuid.uuid4().hex}{suffix}"
    dest = UPLOAD_ROOT / folder / stored_name
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return f"/uploads/{folder}/{stored_name}"


def _cloudinary_upload_enabled() -> bool:
    return all([
        settings.CLOUDINARY_CLOUD_NAME,
        settings.CLOUDINARY_API_KEY,
        settings.CLOUDINARY_API_SECRET,
    ])

async def save_image(file: UploadFile) -> str:
    if file.content_type not in ALLOWED_IMAGES:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, WebP, GIF allowed")
    data = await file.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=400, detail=f"File too large (max {settings.MAX_FILE_SIZE_MB}MB)")

    if _cloudinary_upload_enabled():
        try:
            upload_result = cloudinary.uploader.upload(data, folder="cemtech/images")
            secure_url = upload_result.get("secure_url") or upload_result.get("url")
            if secure_url:
                return secure_url
            logger.warning("Cloudinary image upload returned no URL, saving locally instead.")
        except Exception as exc:
            logger.warning("Cloudinary image upload failed, using local storage fallback: %s", exc)

    return _local_upload_path(data, file.filename, "images", file.content_type)

async def save_video(file: UploadFile) -> str:
    if file.content_type not in ALLOWED_VIDEOS:
        raise HTTPException(status_code=400, detail="Only MP4, WebM, Ogg, MOV video formats allowed")
    data = await file.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=400, detail=f"Video file too large (max {settings.MAX_FILE_SIZE_MB}MB)")

    if _cloudinary_upload_enabled():
        try:
            upload_result = cloudinary.uploader.upload(data, resource_type="video", folder="cemtech/videos")
            secure_url = upload_result.get("secure_url") or upload_result.get("url")
            if secure_url:
                return secure_url
            logger.warning("Cloudinary video upload returned no URL, saving locally instead.")
        except Exception as exc:
            logger.warning("Cloudinary video upload failed, using local storage fallback: %s", exc)

    return _local_upload_path(data, file.filename, "videos", file.content_type)

async def save_product_file(file: UploadFile) -> str:
    return await save_file(file, "products")

async def save_file(file: UploadFile, folder: str = "files") -> str:
    data = await file.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=400, detail=f"File too large (max {settings.MAX_FILE_SIZE_MB}MB)")
    return _local_upload_path(data, file.filename, folder, file.content_type)
