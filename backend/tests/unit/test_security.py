from app.modules.auth.security import create_token, decode_token, hash_password, verify_password


def test_password_hash_round_trip():
    stored = hash_password("Demo-pass-2026")
    assert stored.startswith("scrypt$") and "Demo-pass-2026" not in stored
    assert verify_password("Demo-pass-2026", stored)
    assert not verify_password("demo-pass-2026", stored)
    assert hash_password("Demo-pass-2026") != stored  # salted
    assert not verify_password("x", "garbage")


def test_token_round_trip_tamper_and_expiry():
    token = create_token(7, "driver", "secret", ttl_seconds=60)
    assert decode_token(token, "secret")["sub"] == 7
    assert decode_token(token, "other-secret") is None
    payload, sig = token.split(".")
    assert decode_token(payload + "x." + sig, "secret") is None
    assert decode_token("not-a-token", "secret") is None
    expired = create_token(7, "driver", "secret", ttl_seconds=-1)
    assert decode_token(expired, "secret") is None


def test_production_refuses_the_dev_secret(monkeypatch):
    import pytest
    from pydantic import ValidationError

    from app.core.config import Settings

    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(ValidationError, match="SECRET_KEY must be set"):
        Settings(_env_file=None)
    monkeypatch.setenv("SECRET_KEY", "x" * 48)
    assert Settings(_env_file=None).app_env == "production"
