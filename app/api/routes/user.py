from fastapi import APIRouter, Depends
from api.routes.auth import get_current_user

router = APIRouter(tags=["Users"])

@router.get("/user/profile")
def get_user_profile(current_user = Depends(get_current_user)):
    return {
        "user_id": f"u{current_user.id}",
        "name": current_user.name,
        "email": current_user.email,
    }
