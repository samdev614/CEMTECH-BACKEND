"""
Run once to create the admin user:
  python seed.py
"""
from app.core.database import SessionLocal, engine, Base
from app.core.security import hash_password
from app.core.config import settings
from app.models.user import User
import app.models.blog, app.models.portfolio, app.models.product
import app.models.booking, app.models.contact

# Removed Base.metadata.create_all(bind=engine) 
# Rely on 'python render_start.py' (Alembic) to create tables first.

with SessionLocal() as db:
    existing = db.query(User).filter(User.email == settings.ADMIN_EMAIL).first()
    if existing:
        print(f"Admin already exists: {settings.ADMIN_EMAIL}")
    else:
        admin = User(
            email=settings.ADMIN_EMAIL,
            hashed_password=hash_password(settings.ADMIN_PASSWORD),
            full_name="Admin",
            is_admin=True,
            is_active=True,
        )
        db.add(admin)
        db.commit()
        print(f"Admin created: {settings.ADMIN_EMAIL}")
