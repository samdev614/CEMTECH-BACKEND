from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_password, create_access_token, get_current_user
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserOut

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):

    try:
        # SUPPORT BOTH email OR username (VERY IMPORTANT)
        user = db.query(User).filter(
            (User.email == data.email) | (User.username == data.email)
        ).first()

        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # FIX: make sure field name is correct
        if not verify_password(data.password, user.password_hash):  
            raise HTTPException(status_code=401, detail="Invalid credentials")

        if not user.is_active:
            raise HTTPException(status_code=403, detail="Account disabled")

        token = create_access_token({"sub": str(user.id)})

        return {
            "access_token": token,
            "token_type": "bearer"
        }

    except Exception as e:
        db.rollback()
        print("LOGIN ERROR:", str(e))  
        raise HTTPException(status_code=500, detail="Internal server error")

# @router.post("/login", response_model=TokenResponse)
# def login(data: LoginRequest, db: Session = Depends(get_db)):
#     user = db.query(User).filter(User.email == data.email).first()
#     if not user or not verify_password(data.password, user.hashed_password):
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
#     if not user.is_active:
#         raise HTTPException(status_code=403, detail="Account disabled")
#     token = create_access_token({"sub": str(user.id)})
#     return {"access_token": token, "token_type": "bearer"}

# @router.get("/me", response_model=UserOut)
# def me(current_user=Depends(get_current_user)):
#     return current_user
