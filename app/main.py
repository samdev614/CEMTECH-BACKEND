from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings as app_settings
from app.api.routes import (
    auth,
    blog,
    bookings,
    contact,
    courses,
    documentation,
    gallery,
    mpesa,
    portfolio,
    presets,
    products,
    settings,
    students,
    templates,
    tools,
)
from app.services.upload import UPLOAD_ROOT


def _clean_origin(origin: str | None) -> str | None:
    if not origin:
        return None
    cleaned = origin.strip().rstrip("/")
    if cleaned in {"FRONTEND_URL", "BACKEND_URL"}:
        return None
    return cleaned


CORS_ORIGINS = []
for origin in [
    app_settings.FRONTEND_URL,
    app_settings.BACKEND_URL,
    "https://creativeaglemedia.co.ke",
    "https://www.creativeaglemedia.co.ke",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:5175",
    "http://127.0.0.1:5175",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
]:
    cleaned = _clean_origin(origin)
    if cleaned and cleaned not in CORS_ORIGINS:
        CORS_ORIGINS.append(cleaned)

app = FastAPI()

#cors
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_ROOT)), name="uploads")

app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(blog.router, prefix="/api/blog", tags=["Blog"])
app.include_router(bookings.router, prefix="/api/bookings", tags=["Bookings"])
app.include_router(contact.router, prefix="/api/contact", tags=["Contact"])
app.include_router(courses.router, prefix="/api/courses", tags=["Courses"])
app.include_router(mpesa.product_buy_router, prefix="/api/products", tags=["M-Pesa"])
app.include_router(mpesa.course_buy_router, prefix="/api/courses", tags=["M-Pesa"])
app.include_router(mpesa.util_router, prefix="/api", tags=["M-Pesa Utils"])
app.include_router(students.router, prefix="/api/admin", tags=["Admin"])
app.include_router(documentation.router, prefix="/api/docs", tags=["Documentation"])
app.include_router(gallery.router, prefix="/api/gallery", tags=["Gallery"])
app.include_router(portfolio.router, prefix="/api/portfolio", tags=["Portfolio"])
app.include_router(products.router, prefix="/api/products", tags=["Products"])
app.include_router(templates.router, prefix="/api/templates", tags=["Templates"])
app.include_router(presets.router, prefix="/api/presets", tags=["Presets"])
app.include_router(tools.router, prefix="/api/tools", tags=["Tools"])
app.include_router(settings.router, prefix="/api/settings", tags=["Settings"])
