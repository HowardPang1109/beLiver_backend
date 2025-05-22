# Fastapi進入點
from fastapi import FastAPI
from auth import router as auth_router
from models import Base
from core.db import engine
from api.main import router as api_router

app = FastAPI()
app.include_router(auth_router)
app.include_router(api_router)

# 建立資料表
Base.metadata.create_all(bind=engine)