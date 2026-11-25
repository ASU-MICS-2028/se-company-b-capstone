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


def test_datetimes_round_trip_as_utc(session):
    """SQLite drops offsets; UTCDateTime must hand back aware UTC (matching engine compares)."""
    from datetime import UTC, datetime, timedelta, timezone

    from app.models import OdometerReading

    user = User(email="t@example.com", password_hash="x", full_name="T")
    session.add(user)
    session.flush()
    car = _vehicle(owner_id=user.id)
    session.add(car)
    session.flush()
    accra_plus_one = datetime(2026, 11, 23, 9, 0, tzinfo=timezone(timedelta(hours=1)))
    session.add(OdometerReading(vehicle_id=car.id, odometer_km=48000, read_at=accra_plus_one))
    session.commit()
    session.expire_all()

    reading = session.query(OdometerReading).one()
    assert reading.read_at == datetime(2026, 11, 23, 8, 0, tzinfo=UTC)
    assert reading.read_at.tzinfo is not None
    assert session.get(User, user.id).created_at.tzinfo is not None  # server default too


def test_naive_datetimes_are_rejected(session):
    from datetime import datetime

    from sqlalchemy.exc import StatementError

    from app.models import OdometerReading

    session.add(OdometerReading(vehicle_id=1, odometer_km=1, read_at=datetime(2026, 1, 1)))
    with pytest.raises(StatementError, match="naive datetime"):
        session.commit()
