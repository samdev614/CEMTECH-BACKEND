from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy.orm import Session
from sqlalchemy.exc import ProgrammingError

from app.core.database import SessionLocal
from app.api.routes import (
    auth, blog, bookings, contact, courses, documentation, mpesa,
    portfolio, presets, products, settings, templates, tools
)
from app.models.settings import ServiceMedia # Import ServiceMedia model


# Define the _ensure_defaults function here, or import it if it's in a utility file
VALID_KEYS = {"software_dev", "video_prod", "marketing"}
OLD_KEYS = {"Web_dev", "web_dev"}  # Deprecated keys to migrate

def _ensure_defaults_settings(db: Session):
    """Seed the three rows if they don't exist yet and migrate old keys."""
    # Migrate old "Web_dev" or "web_dev" to "software_dev"
    old_entry = db.query(ServiceMedia).filter(ServiceMedia.key.in_(OLD_KEYS)).first()
    if old_entry:
        old_entry.key = "software_dev"
        db.commit()
    
    # Create missing valid keys
    for key in VALID_KEYS:
        if not db.query(ServiceMedia).filter(ServiceMedia.key == key).first():
            db.add(ServiceMedia(key=key, media_url=None, media_type="image"))
            db.commit()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup event
    db = SessionLocal()
    try:
        _ensure_defaults_settings(db)
    except ProgrammingError as e:
        # Table doesn't exist yet - migrations may not have run
        # Log the issue but don't crash the app
        print(f"Warning: Could not seed defaults - {e}")
        print("This is OK during initial migrations. Service media table will be created on next startup.")
    finally:
        db.close()
    yield
    # Shutdown event (optional)

app = FastAPI(lifespan=lifespan)

# Include your routers
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(blog.router, prefix="/api/blog", tags=["Blog"])
app.include_router(bookings.router, prefix="/api/bookings", tags=["Bookings"])
app.include_router(contact.router, prefix="/api/contact", tags=["Contact"])
app.include_router(courses.router, prefix="/api/courses", tags=["Courses"])
app.include_router(documentation.router, prefix="/api/documentation", tags=["Documentation"])
app.include_router(mpesa.buy_router, prefix="/api/products", tags=["M-Pesa"])
app.include_router(mpesa.util_router, prefix="/api", tags=["M-Pesa Utils"])
app.include_router(portfolio.router, prefix="/api/portfolio", tags=["Portfolio"])
app.include_router(presets.router, prefix="/api/presets", tags=["Presets"])
app.include_router(products.router, prefix="/api/products", tags=["Products"])
app.include_router(settings.router, prefix="/api/settings", tags=["Settings"])
app.include_router(templates.router, prefix="/api/templates", tags=["Templates"])
app.include_router(tools.router, prefix="/api/tools", tags=["Tools"])