"""Password hashing and access tokens, stdlib only (hashlib.scrypt + HMAC-SHA256).

Password format: scrypt$<n>$<r>$<p>$<salt b64>$<hash b64>
Token format:    <payload b64url>.<HMAC-SHA256 signature b64url>, payload {"sub", "role", "exp"}
"""

import base64
import hashlib
import hmac
import json
import secrets
import time

N, R, P, DKLEN = 2**14, 8, 1, 32


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=N, r=R, p=P, dklen=DKLEN)
    return f"scrypt${N}${R}${P}${_b64(salt)}${_b64(digest)}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, n, r, p, salt, digest = stored.split("$")
        if algo != "scrypt":
            return False
        candidate = hashlib.scrypt(
            password.encode(), salt=_unb64(salt), n=int(n), r=int(r), p=int(p), dklen=DKLEN
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(candidate, _unb64(digest))


# Verified against when the login is unknown, so both failures take the same time.
DUMMY_HASH = hash_password(secrets.token_urlsafe(16))


def create_token(user_id: int, role: str, secret: str, ttl_seconds: int) -> str:
    payload = _b64(
        json.dumps({"sub": user_id, "role": role, "exp": int(time.time()) + ttl_seconds}).encode()
    )
    return f"{payload}.{_sign(payload, secret)}"


def decode_token(token: str, secret: str) -> dict | None:
    """Payload if the signature is valid and the token hasn't expired, else None."""
    try:
        payload, signature = token.split(".")
        if not hmac.compare_digest(signature, _sign(payload, secret)):
            return None
        data = json.loads(_unb64(payload))
    except (ValueError, TypeError):
        return None
    return data if data.get("exp", 0) > time.time() else None


def _sign(payload: str, secret: str) -> str:
    return _b64(hmac.new(secret.encode(), payload.encode(), hashlib.sha256).digest())
