from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.core.config import settings
from app.core.database import engine, Base
from app.api.routes import auth, blog, portfolio, products, bookings, contact
from app.api.routes.mpesa import buy_router as mpesa_buy, util_router as mpesa_util
from app.utils.create_admin import create_admin
import app.models.blog
import app.models.portfolio
import app.models.product
import app.models.booking
import app.models.contact

app = FastAPI(
    title="CEMTECH API",
    description="Backend API for CEMTECH portfolio website",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://creativeaglemedia.co.ke",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(blog.router, prefix="/api/blog", tags=["Blog"])
app.include_router(portfolio.router, prefix="/api/portfolio", tags=["Portfolio"])
app.include_router(products.router, prefix="/api/products", tags=["Products"])
app.include_router(mpesa_buy, prefix="/api/products", tags=["M-Pesa"])
app.include_router(bookings.router, prefix="/api/bookings", tags=["Bookings"])
app.include_router(contact.router, prefix="/api/contact", tags=["Contact"])
app.include_router(mpesa_util, prefix="/api", tags=["Utils"])

@app.on_event("startup")
def startup_event():
    create_admin()

# Serve uploaded files
uploads_path = Path(settings.UPLOAD_DIR)
uploads_path.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_path)), name="uploads")