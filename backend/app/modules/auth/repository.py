from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.auth.models import User


def get(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def get_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def get_by_phone(db: Session, phone: str) -> User | None:
    return db.scalar(select(User).where(User.phone == phone))


def add(db: Session, user: User) -> User:
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
