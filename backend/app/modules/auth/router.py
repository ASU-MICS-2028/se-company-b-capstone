"""Auth routes (#49): register, login, me."""

from fastapi import APIRouter, status

from app.core.db import DbSession
from app.core.errors import ERRORS
from app.modules.auth import service
from app.modules.auth.deps import CurrentUser
from app.modules.auth.schemas import LoginRequest, RegisterRequest, TokenOut, UserOut

router = APIRouter(prefix="/auth", tags=["auth"], responses=ERRORS)


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: DbSession) -> TokenOut:
    """US-01. Creates a **driver** and logs them in. 409 `account_exists` if the email or
    phone is taken ("An account with this email exists")."""
    return service.register(db, body)


@router.post("/login")
def login(body: LoginRequest, db: DbSession) -> TokenOut:
    """`login` is an email or a phone number. 401 `invalid_credentials`, with the same message
    for an unknown login and a wrong password."""
    return service.login(db, body)


@router.get("/me")
def me(user: CurrentUser) -> UserOut:
    return UserOut.model_validate(user, from_attributes=True)
