from fastapi import APIRouter, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from jose import JWTError, jwt
import os
from crud.crud_user import get_user_by_email
from core.db import get_db
from dotenv import load_dotenv

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
            return JSONResponse(status_code=401, content={"error": "Invalid token"})
    except JWTError:
        return JSONResponse(status_code=401, content={"error": "Invalid token"})

    user = get_user_by_email(db, email=email)
    if user is None:
        return JSONResponse(status_code=401, content={"error": "User not found"})

    return user

@router.get("/user/profile")
def get_user_profile(current_user = Depends(get_current_user)):
    # current_user 可能是 JSONResponse（錯誤情況），先檢查型別
    if isinstance(current_user, JSONResponse):
        return current_user

    return {
        "user_id": f"u{current_user.id}",
        "name": current_user.name,
        "email": current_user.email,
        "timezone": "Asia/Taipei"
    }
