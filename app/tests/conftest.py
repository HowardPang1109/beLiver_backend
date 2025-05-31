import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import models  # 👈 這裡要 import 整個 models module
from app.core.db import Base, get_db
from app.main import app

SQLALCHEMY_TEST_DB_URL = "sqlite:///./test.db"

# 確保乾淨環境
if os.path.exists("test.db"):
    os.remove("test.db")

engine = create_engine(SQLALCHEMY_TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 建立資料表（前提是 models 有正確匯入）
Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

    if os.path.exists("test.db"):
        os.remove("test.db")
