from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from app.models import Base
from app.core.db import engine
from app.api.main import router as api_router 

app = FastAPI()

app.include_router(api_router)


Base.metadata.create_all(bind=engine)