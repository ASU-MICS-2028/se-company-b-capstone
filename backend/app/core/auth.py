"""Auth dependencies. Stub until #49: declares the bearer scheme so Swagger shows locks."""

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

bearer = HTTPBearer(auto_error=False)

# TODO(#49): decode token, load user, 401 if missing; require_role("admin") for admin routes.
BearerToken = Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]
