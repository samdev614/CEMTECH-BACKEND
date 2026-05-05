from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.core.config import settings
from app.core.database import engine, Base
from app.api.routes import auth, blog, portfolio, products, bookings, contact, documentation
from app.api.routes import templates, presets, courses, tools
from app.api.routes.mpesa import buy_router as mpesa_buy, util_router as mpesa_util
from app.api.routes import settings as settings_routes
from app.utils.create_admin import create_admin
import app.models.blog
import app.models.portfolio
import app.models.product
import app.models.template
import app.models.preset
import app.models.course
import app.models.tool
import app.models.booking
import app.models.contact
import app.models.user
import app.models.documentation
import app.models.settings

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
         "https://creativeaglemedia.co.ke",
    ],
        # "https://creativeaglemedia.co.ke",
     
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
app.include_router(templates.router, prefix="/api/templates", tags=["Templates"])
app.include_router(presets.router, prefix="/api/presets", tags=["Presets"])
app.include_router(courses.router, prefix="/api/courses", tags=["Courses"])
app.include_router(tools.router, prefix="/api/tools", tags=["Tools"])
app.include_router(bookings.router, prefix="/api/bookings", tags=["Bookings"])
app.include_router(contact.router, prefix="/api/contact", tags=["Contact"])
app.include_router(documentation.router, prefix="/api/docs", tags=["Documentation"])
app.include_router(settings_routes.router, prefix="/api/settings", tags=["Settings"])
app.include_router(mpesa_util, prefix="/api", tags=["Utils"])

@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)
    create_admin()

# Serve uploaded files
uploads_path = Path(settings.UPLOAD_DIR)
uploads_path.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_path)), name="uploads")