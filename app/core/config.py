from pydantic_settings import BaseSettings
from pydantic import field_validator
from pathlib import Path

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""

    ADMIN_EMAIL: str = "admin@gmail.com"
    ADMIN_PASSWORD: str = "password"

    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE_MB: int = 50

    FRONTEND_URL: str = "https://creativeaglemedia.co.ke"
    BACKEND_URL: str = "https://cemtech-backend.onrender.com"
    # Resend email
    RESEND_API_KEY: str = ""
    EMAIL_FROM: str = "CEMTECH <noreply@yourdomain.com>"
    ADMIN_EMAIL_NOTIFY: str = ""   # where to receive contact/order alerts

    # M-Pesa Daraja
    MPESA_CONSUMER_KEY: str = ""
    MPESA_CONSUMER_SECRET: str = ""
    MPESA_SHORTCODE: str = "174379"       # Daraja sandbox default
    MPESA_PASSKEY: str = ""
    MPESA_CALLBACK_URL: str = "https://creativeaglemedia.co.ke/api/mpesa/callback"
    MPESA_ENV: str = "sandbox"            # "sandbox" or "production"

    @field_validator("DATABASE_URL")
    @classmethod
    def fix_postgres_url(cls, v: str) -> str:
        # Render provides postgres:// but SQLAlchemy 2.x requires postgresql://
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql://", 1)
        return v

    class Config:
        env_file = ".env"

settings = Settings()

UPLOAD_PATH = Path(settings.UPLOAD_DIR)
UPLOAD_PATH.mkdir(parents=True, exist_ok=True)
(UPLOAD_PATH / "images").mkdir(exist_ok=True)
(UPLOAD_PATH / "products").mkdir(exist_ok=True)
