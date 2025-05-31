from fastapi import APIRouter, FastAPI
from app.api.routes import auth, user, task, file, assistant, project
from fastapi.staticfiles import StaticFiles

router = APIRouter()

# app = FastAPI()
# app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
router.include_router(auth.router, tags=["Auth"])
router.include_router(user.router, tags=["User"])
router.include_router(task.router, tags=["Tasks"])
router.include_router(file.router, tags=["Files"])
router.include_router(assistant.router, tags=["Assistant"])
router.include_router(project.router, tags=["Project"])


# app.include_router(router)