"""Stub routes (contract v1). Real logic: #49."""

from fastapi import APIRouter, status

from app.core.auth import BearerToken
from app.core.errors import ERRORS
from app.modules.auth.schemas import LoginRequest, RegisterRequest, TokenOut, UserOut

router = APIRouter(prefix="/auth", tags=["auth"], responses=ERRORS)

_AMA = UserOut(id=1, full_name="Ama Mensah", email="ama@example.com", phone=None, role="driver")


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest) -> TokenOut:
    """US-01. 409 `account_exists` if the email or phone is taken. Logs the user in."""
    return TokenOut(access_token="stub-token", user=_AMA)


@router.post("/login")
def login(body: LoginRequest) -> TokenOut:
    """401 `invalid_credentials` on a wrong login or password (same message for both)."""
    return TokenOut(access_token="stub-token", user=_AMA)


@router.get("/me")
def me(_: BearerToken) -> UserOut:
    return _AMA
