from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_password, hash_password, create_access_token, get_current_user
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserOut

router = APIRouter()


@router.post("/register", response_model=TokenResponse)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new admin user"""
    # Normalize email
    email = data.email.strip().lower()

    # Check if user already exists
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Hash password
    hashed_password = hash_password(data.password)

    # Create new admin user
    new_user = User(
        email=email,
        hashed_password=hashed_password,
        full_name=data.full_name,
        is_active=True,
        is_admin=True  # New registrations are admin users
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Create JWT token
    token = create_access_token({"sub": str(new_user.id)})

    return {
        "access_token": token,
        "token_type": "bearer"
    }


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    # Normalize email (prevents hidden mismatch issues)
    email = data.email.strip().lower()

    user = db.query(User).filter(User.email == email).first()

    # Explicit checks (better debugging + avoids silent failures)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Ensure password exists in DB
    if not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User password not set correctly"
        )

    # Verify password safely
    if not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Check if account is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account disabled"
        )
    # Create JWT token
    token = create_access_token({"sub": str(user.id)})

    return {
        "access_token": token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserOut)
def me(current_user=Depends(get_current_user)):
    return current_user
