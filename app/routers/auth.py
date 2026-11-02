from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Role, CustomerProfile, Cart
from app.schemas import RegisterIn, UserOut, TokenOut
from app.security import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserOut, status_code=201)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == data.email.lower()).first():
        raise HTTPException(409, "Email is already registered")
    user = User(full_name=data.full_name.strip(), email=data.email.lower(), password_hash=hash_password(data.password), role=Role.CUSTOMER)
    db.add(user); db.flush()
    db.add(CustomerProfile(user_id=user.id)); db.add(Cart(user_id=user.id))
    db.commit(); db.refresh(user)
    return user

@router.post("/login", response_model=TokenOut)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form.username.lower()).first()
    if not user or not verify_password(form.password, user.password_hash) or not user.is_active:
        raise HTTPException(status_code=401, detail="Incorrect email or password", headers={"WWW-Authenticate":"Bearer"})
    return {"access_token":create_access_token(user), "token_type":"bearer"}

@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
