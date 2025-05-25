from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from models import Base
from core.db import engine
from api.main import router as api_router 

app = FastAPI()

app.include_router(api_router)


Base.metadata.create_all(bind=engine)