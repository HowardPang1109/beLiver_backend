from fastapi import APIRouter, responses, Depends
from sqlalchemy.orm import Session
from core.db import SessionLocal
from models import User
from utils import verify_password, hash_password, create_jwt_token

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/auth/register")
def register_user(payload: dict, db: Session = Depends(get_db)):
    """
    curl -X POST "http://localhost:8000/auth/register" \
    -H "Content-Type: application/json" \
    -d '{
            "name": "Sandy",
            "email": "sandy@example.com",
            "password": "Password123"
        }'
    """
    name = payload.get("name")
    email = payload.get("email")
    password = payload.get("password")

    if not password or len(password) < 8:
        return responses.JSONResponse(
            status_code=400, content={"error": "Password must be at least 8 characters"}
        )

    if not email or not name:
        return responses.JSONResponse(
            status_code=400, content={"error": "Name and email are required"}
        )

    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        return responses.JSONResponse(
            status_code=409, content={"error": "Email already registered"}
        )

    hashed = hash_password(password)

    new_user = User(email=email, name=name, hashed_password=hashed)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)  # 讓 new_user.id 可用

    token = create_jwt_token({"sub": email})

    return responses.JSONResponse(
        status_code=201,
        content={
            "user_id": new_user.id,
            "name": name,
            "token": token,
            "message": "Registration successful",
        },
    )

@router.post("/auth/login")
def login_user(payload: dict, db: Session = Depends(get_db)):
    """
    curl -X POST "http://localhost:8000/auth/login" \
    -H "Content-Type: application/json" \
    -d '{
            "email": "sandy@example.com",
            "password": "Password123"
        }'
      """
    email = payload.get("email")
    password = payload.get("password")

    if not email or not password:
        return responses.JSONResponse(
            status_code=400, content={"error": "Email and password required"}
        )

    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return responses.JSONResponse(
            status_code=401, content={"error": "Invalid credentials"}
        )

    token = create_jwt_token({"sub": user.email})

    return responses.JSONResponse(
        status_code=200,
        content={
            "user_id": f"u{user.id}",
            "name": user.name,
            "token": token,
            "message": "Login successful",
        },
    )
