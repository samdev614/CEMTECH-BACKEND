from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import hash_password
from app.core.config import settings

def create_admin():
    db: Session = SessionLocal()

    email = settings.ADMIN_EMAIL
    password = settings.ADMIN_PASSWORD

    if not email or not password:
        print( "Admin credentials not set in .env")
        return

    existing_user = db.query(User).filter(User.email == email).first()

    if existing_user:
        print("Admin already exists")
        return

    hashed_password = hash_password(password)

    admin = User(
        email=email,
        hashed_password=hashed_password,
        is_active=True
    )

    db.add(admin)
    db.commit()
    db.close()

    print("Admin user created")