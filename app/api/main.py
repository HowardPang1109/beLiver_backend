from fastapi import APIRouter
from app.api.routes import project, auth, user  # ← 注意從 routes 導入

router = APIRouter()

router.include_router(project.router, prefix="/project", tags=["Project"])
router.include_router(auth.router, prefix="/auth", tags=["Auth"])
router.include_router(user.router, prefix="/user", tags=["User"])
