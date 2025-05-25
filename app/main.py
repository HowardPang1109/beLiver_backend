# Fastapi進入點
from fastapi import FastAPI, Depends
from fastapi.security import HTTPBearer
from fastapi.openapi.utils import get_openapi

from api.auth import router as auth_router
from api.user import router as api_router
from api.task import router as task_router
from api.file import router as file_router 
from api.assistant import router as assistant_router 
from models import Base
from core.db import engine

app = FastAPI()

app.include_router(auth_router)
app.include_router(api_router)
app.include_router(task_router)
app.include_router(file_router) 
app.include_router(assistant_router)

# 建立資料表
Base.metadata.create_all(bind=engine)