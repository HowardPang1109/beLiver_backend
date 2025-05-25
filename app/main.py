# Fastapi進入點
from fastapi import FastAPI
from models import Base
from core.db import engine
from api.main import router as api_router  # ← 請注意這邊引用的是 app.api.main

app = FastAPI()

app.include_router(api_router)


# 建立資料表
Base.metadata.create_all(bind=engine)