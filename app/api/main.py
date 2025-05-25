from fastapi import APIRouter
from api.routes import auth, user, task, file, assistant

router = APIRouter()

router.include_router(auth.router, tags=["Auth"])
router.include_router(user.router, tags=["User"])
router.include_router(task.router, tags=["Tasks"])
router.include_router(file.router, tags=["File"])
router.include_router(assistant.router, tags=["Assistant"])
