from pydantic_settings import BaseSettings
from pydantic import field_validator
from pathlib import Path

BACKEND_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
print(f"DEBUG: BACKEND_ENV_FILE path: {BACKEND_ENV_FILE}") # New debug print

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
    MAX_FILE_SIZE_MB: int = 500 # Increased max file size for videos

    FRONTEND_URL: str = "FRONTEND_URL"   # https://creativeaglemedia.co.ke
    BACKEND_URL: str = "BACKEND_URL" # https://cemtech-backend.onrender.com
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
    MPESA_STATUS_QUERY_COOLDOWN_SECONDS: int = 60

    @field_validator("DATABASE_URL")
    @classmethod
    def fix_postgres_url(cls, v: str) -> str:
        # Render provides postgres:// but SQLAlchemy 2.x requires postgresql://
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql://", 1)
        return v

    @field_validator(
        "DATABASE_URL",
        "SECRET_KEY",
        "CLOUDINARY_CLOUD_NAME",
        "CLOUDINARY_API_KEY",
        "CLOUDINARY_API_SECRET",
        "ADMIN_EMAIL",
        "ADMIN_PASSWORD",
        "UPLOAD_DIR",
        "FRONTEND_URL",
        "BACKEND_URL",
        "RESEND_API_KEY",
        "EMAIL_FROM",
        "ADMIN_EMAIL_NOTIFY",
        "MPESA_CONSUMER_KEY",
        "MPESA_CONSUMER_SECRET",
        "MPESA_SHORTCODE",
        "MPESA_PASSKEY",
        "MPESA_CALLBACK_URL",
        mode="before",
    )
    @classmethod
    def strip_string_values(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v

    @field_validator("MPESA_ENV", mode="before")
    @classmethod
    def normalize_mpesa_env(cls, v):
        if isinstance(v, str):
            return v.strip().lower()
        return v

    class Config:
        env_file = str(BACKEND_ENV_FILE)

settings = Settings()
print(f"DEBUG: MAX_FILE_SIZE_MB loaded from config: {settings.MAX_FILE_SIZE_MB}MB") # Debug print
