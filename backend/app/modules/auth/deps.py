"""FastAPI dependencies for the signed-in user (ADR-005, Dependency Injection).

def route(user: CurrentUser): ...
@router.get(..., dependencies=[require_role("admin")])
"""

from typing import Annotated

from fastapi import Depends

from app.core.auth import BearerToken
from app.core.config import get_settings
from app.core.db import DbSession
from app.core.errors import ApiError
from app.modules.auth import repository
from app.modules.auth.models import User
from app.modules.auth.security import decode_token


def current_user(creds: BearerToken, db: DbSession) -> User:
    payload = decode_token(creds.credentials, get_settings().secret_key) if creds else None
    user = repository.get(db, payload["sub"]) if payload else None
    if user is None:
        raise ApiError(401, "unauthorized", "Sign in to continue")
    return user


CurrentUser = Annotated[User, Depends(current_user)]


def require_role(*roles: str):
    def check(user: CurrentUser) -> User:
        if user.role not in roles:
            raise ApiError(403, "forbidden", "You don't have access to this")
        return user

    return Depends(check)
