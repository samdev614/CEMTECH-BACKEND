from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.security import hash_password, require_admin
from app.models.user import User
from app.schemas.user import UserCreate, UserOut

router = APIRouter()

@router.post("/", response_model=UserOut)
def create_user(
    data: UserCreate, 
    db: Session = Depends(get_db), 
    current_admin = Depends(require_admin)
):
    """
    Create a new user or administrator. 
    Restricted to existing admins to prevent unauthorized access.
    """
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        is_active=data.is_active,
        is_admin=data.is_admin
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.get("/", response_model=List[UserOut])
def list_users(db: Session = Depends(get_db), _=Depends(require_admin)):
    """List all registered users."""
    return db.query(User).all()

@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    """Remove a user account."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"message": "User deleted"}