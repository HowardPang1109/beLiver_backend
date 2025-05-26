from fastapi import APIRouter, Depends
from crud.crud_user import get_current_user

router = APIRouter(tags=["Users"])

@router.get("/users/profile")
def get_user_profile(current_user = Depends(get_current_user)):
    return {
        "user_id": f"u{current_user.id}",
        "name": current_user.name,
        "email": current_user.email,
    }
