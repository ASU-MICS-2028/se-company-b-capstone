from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import ApiError
from app.modules.auth import repository
from app.modules.auth.models import User
from app.modules.auth.schemas import (
    LoginRequest,
    RegisterRequest,
    TokenOut,
    UserOut,
    normalise_phone,
)
from app.modules.auth.security import DUMMY_HASH, create_token, hash_password, verify_password

ACCOUNT_EXISTS = {
    "email": "An account with this email exists",  # US-01 wording
    "phone": "An account with this phone number exists",
}
INVALID_MESSAGE = "Incorrect email, phone number or password"  # same for unknown login


def issue_token(user: User) -> TokenOut:
    s = get_settings()
    token = create_token(user.id, user.role, s.secret_key, s.token_ttl_minutes * 60)
    return TokenOut(
        access_token=token,
        expires_in=s.token_ttl_minutes * 60,
        user=UserOut.model_validate(user, from_attributes=True),
    )


def register(db: Session, body: RegisterRequest, role: str = "driver") -> TokenOut:
    """Self sign-up always creates a driver; other roles come from create_user (CLI)."""
    if body.email and repository.get_by_email(db, body.email):
        raise ApiError(409, "account_exists", ACCOUNT_EXISTS["email"], {"field": "email"})
    if body.phone and repository.get_by_phone(db, body.phone):
        raise ApiError(409, "account_exists", ACCOUNT_EXISTS["phone"], {"field": "phone"})
    user = User(
        full_name=body.full_name,
        email=body.email,
        phone=body.phone,
        password_hash=hash_password(body.password),
        role=role,
    )
    try:
        repository.add(db, user)
    except IntegrityError:  # lost a race with a concurrent sign-up
        db.rollback()
        raise ApiError(409, "account_exists", ACCOUNT_EXISTS["email"]) from None
    return issue_token(user)


def login(db: Session, body: LoginRequest) -> TokenOut:
    login_id = body.login.strip()
    if login_id.startswith("+"):
        user = repository.get_by_phone(db, normalise_phone(login_id))
    else:
        user = repository.get_by_email(db, login_id.lower())
    if not verify_password(body.password, user.password_hash if user else DUMMY_HASH) or not user:
        raise ApiError(401, "invalid_credentials", INVALID_MESSAGE)
    return issue_token(user)
