import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.db import create_all
from app.models import User, Vehicle


@pytest.fixture
def session(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'schema.db'}")
    create_all(engine)
    with Session(engine) as s:
        yield s
    engine.dispose()


def _vehicle(**overrides):
    fields = dict(make="Toyota", model="Corolla", model_year=2025, powertrain="petrol")
    return Vehicle(**(fields | overrides))


def test_manual_vehicle_without_catalogue_entry(session):
    user = User(email="ama@example.com", password_hash="x", full_name="Ama")
    session.add(user)
    session.flush()
    session.add(_vehicle(owner_id=user.id, make="Nissan", model="Almera"))
    session.commit()  # catalogue_id is optional; defaults fill market/body/condition


def test_foreign_keys_are_enforced(session):
    session.add(_vehicle(owner_id=999))
    with pytest.raises(IntegrityError):
        session.commit()


def test_enum_columns_reject_unknown_values(session):
    session.add(User(email="x@example.com", password_hash="x", full_name="X", role="owner"))
    with pytest.raises(IntegrityError):
        session.commit()


def test_user_needs_email_or_phone(session):
    session.add(User(phone="+233200000000", password_hash="x", full_name="Kojo"))
    session.commit()
    session.add(User(password_hash="x", full_name="Nobody"))
    with pytest.raises(IntegrityError):
        session.commit()
