"""US-01 sign-up and login (#49). AT-US01-1/2 and AC-01/AC-04 from the test plan."""

import pytest
from sqlalchemy import select

from app.core.db import get_db
from app.main import app
from app.modules.auth.deps import require_role
from app.modules.auth.models import User

V = "/api/v1/auth"
AMA = {"full_name": "Ama Mensah", "email": "Ama@Example.com", "password": "Demo-pass-2026"}


def register(client, **overrides):
    return client.post(f"{V}/register", json=AMA | overrides)


def bearer(res):
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def test_sign_up_logs_the_driver_in(client):
    """AT-US01-1: logged in without a separate login step."""
    res = register(client)
    assert res.status_code == 201
    body = res.json()
    assert body["user"]["role"] == "driver"
    assert body["user"]["email"] == "ama@example.com"  # normalised
    assert body["expires_in"] > 0
    me = client.get(f"{V}/me", headers=bearer(res))
    assert me.status_code == 200 and me.json()["id"] == body["user"]["id"]


def test_duplicate_email_is_rejected_with_story_wording(client):
    """AT-US01-2: exact message, 409, and no second account."""
    register(client)
    res = register(client, email="ama@example.com", full_name="Someone else")
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "account_exists"
    assert res.json()["error"]["message"] == "An account with this email exists"
    assert "access_token" not in res.json()
    login = client.post(
        f"{V}/login", json={"login": "ama@example.com", "password": AMA["password"]}
    )
    assert login.json()["user"]["full_name"] == "Ama Mensah"


def test_sign_up_with_phone_only_and_log_in_with_spaces(client):
    res = register(client, email=None, phone="+233 20 000 0001")
    assert res.status_code == 201
    assert res.json()["user"]["phone"] == "+233200000001"
    login = client.post(
        f"{V}/login", json={"login": "+233 20 000-0001", "password": AMA["password"]}
    )
    assert login.status_code == 200
    dup = register(client, email=None, phone="+233200000001")
    assert dup.status_code == 409 and "phone" in dup.json()["error"]["message"]


@pytest.mark.parametrize(
    "overrides",
    [
        {"email": None},  # neither email nor phone
        {"phone": "0200000001"},  # not international
        {"password": "short"},
        {"full_name": "   "},
        {"email": "not-an-email"},
    ],
    ids=["no-contact", "local-phone", "short-password", "blank-name", "bad-email"],
)
def test_invalid_sign_up_is_422(client, overrides):
    assert register(client, **overrides).status_code == 422


def test_self_sign_up_cannot_choose_a_role(client):
    res = register(client, role="admin")
    assert res.json()["user"]["role"] == "driver"


def test_login_failures_share_one_message(client):
    register(client)
    wrong = client.post(f"{V}/login", json={"login": "ama@example.com", "password": "nope-nope"})
    unknown = client.post(f"{V}/login", json={"login": "x@example.com", "password": "nope-nope"})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json()["error"] == unknown.json()["error"]


@pytest.mark.parametrize("header", [None, "Bearer junk", "Basic abc"])
def test_me_requires_a_valid_token(client, header):
    headers = {"Authorization": header} if header else {}
    res = client.get(f"{V}/me", headers=headers)
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "unauthorized"


def test_password_is_stored_hashed(client):
    """AC-04."""
    register(client)
    db = next(app.dependency_overrides[get_db]())
    user = db.scalar(select(User))
    assert user.password_hash.startswith("scrypt$")
    assert AMA["password"] not in user.password_hash


def test_require_role_blocks_other_roles(client):
    """AC-03 building block: admin-only routes return 403 to drivers."""
    from fastapi import APIRouter

    probe = APIRouter()

    @probe.get("/_probe/admin", dependencies=[require_role("admin")])
    def _admin_only():
        return {"ok": True}

    app.include_router(probe)
    try:
        res = client.get("/_probe/admin", headers=bearer(register(client)))
        assert res.status_code == 403 and res.json()["error"]["code"] == "forbidden"
    finally:
        app.router.routes[:] = [r for r in app.router.routes if r.path != "/_probe/admin"]
