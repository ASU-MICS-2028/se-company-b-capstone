from datetime import datetime

from sqlalchemy import CheckConstraint, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, UTCDateTime, choice

ROLES = ("driver", "mechanic", "admin")


class User(Base):
    """Sign up with email or phone (US-01); at least one is required."""

    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("email IS NOT NULL OR phone IS NOT NULL", name="email_or_phone"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str | None] = mapped_column(String(254), unique=True)
    phone: Mapped[str | None] = mapped_column(String(20), unique=True)  # E.164, e.g. +233...
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(120))
    role: Mapped[str] = mapped_column(choice("user_role", *ROLES), default="driver")
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, server_default=func.now())
