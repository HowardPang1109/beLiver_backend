# 使用者table crud
from sqlalchemy.orm import Session
from models import User

def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()