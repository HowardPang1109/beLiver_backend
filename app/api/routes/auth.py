from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt
import os
from crud.crud_user import get_user_by_email
from core.db import get_db
from utils import verify_password, hash_password, create_jwt_token
from dotenv import load_dotenv
from models import User

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
router = APIRouter()
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = get_user_by_email(db, email=email)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return user


@router.post("/auth/register")
def register_user(payload: dict, db: Session = Depends(get_db)):
    name = payload.get("name")
    email = payload.get("email")
    password = payload.get("password")

    if not password or len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    if not email or not name:
        raise HTTPException(status_code=400, detail="Name and email are required")

    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=409, detail="Email already registered")

    hashed = hash_password(password)

    new_user = User(email=email, name=name, hashed_password=hashed)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)  # 讓 new_user.id 可用

    token = create_jwt_token({"sub": email})

    return {
        "user_id": new_user.id,
        "name": name,
        "token": token,
        "message": "Registration successful",
    }


@router.post("/auth/login")
def login_user(payload: dict, db: Session = Depends(get_db)):
    email = payload.get("email")
    password = payload.get("password")

    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password required")

    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_jwt_token({"sub": user.email})

    return {
        "user_id": f"u{user.id}",
        "name": user.name,
        "token": token,
        "message": "Login successful",
    }
