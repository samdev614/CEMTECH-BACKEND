from sqlalchemy import func
from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import hash_password
from app.core.config import settings

def create_admin():
    email = settings.ADMIN_EMAIL.strip().lower()
    password = settings.ADMIN_PASSWORD

    if not email or not password:
        print("Admin credentials not set")
        return

    hashed_password = hash_password(password)

    with SessionLocal() as db:
        existing_user = (
            db.query(User)
            .filter(func.lower(User.email) == email)
            .first()
        )

        if existing_user:
            existing_user.email = email
            existing_user.hashed_password = hashed_password
            existing_user.is_active = True
            existing_user.is_admin = True
            if not existing_user.full_name:
                existing_user.full_name = "Admin"
            db.commit()
            print(f"Admin user synced: {email}")
            return

        admin = User(
            email=email,
            hashed_password=hashed_password,
            full_name="Admin",
            is_active=True,
            is_admin=True,
        )

        db.add(admin)
        db.commit()
        print(f"Admin user created: {email}")
