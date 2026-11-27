"""Odometer readings used by other modules (ADR-001: call the service, not the tables).
The full odometer and service-log write paths (rollback checks, US-04) are #82."""

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.service_logs.models import OdometerReading


def record_reading(db: Session, vehicle_id: int, km: Decimal, read_at: datetime | None = None):
    reading = OdometerReading(
        vehicle_id=vehicle_id, odometer_km=km, read_at=read_at or datetime.now(UTC)
    )
    db.add(reading)
    return reading


def latest_reading(db: Session, vehicle_id: int) -> OdometerReading | None:
    return db.scalar(
        select(OdometerReading)
        .where(OdometerReading.vehicle_id == vehicle_id)
        .order_by(OdometerReading.read_at.desc(), OdometerReading.id.desc())
        .limit(1)
    )
