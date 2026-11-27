from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, UTCDateTime, choice

ODOMETER_SOURCES = ("manual", "obd")  # OBD-II is future work; field exists so it can land later.

# Service-history keys. R10 tracks engine and cabin air filters separately (rule spec).
# Confirmed by G&I (#67). `engine_and_cabin_air_filter` is a rule service_type, not a key.
SERVICE_KEYS = (
    "engine_oil_and_filter",
    "engine_oil",
    "tyre_rotation",
    "brake_inspection",
    "cabin_air_filter",
    "engine_air_filter",
    "brake_fluid",
    "other",
)


class OdometerReading(Base):
    """Timestamped reading. Older than 30 days = stale for distance (rule spec, step 1)."""

    __tablename__ = "odometer_readings"

    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(
        ForeignKey("vehicles.id", ondelete="CASCADE"), index=True
    )
    odometer_km: Mapped[Decimal] = mapped_column(Numeric(9, 1))
    read_at: Mapped[datetime] = mapped_column(UTCDateTime)  # UTC
    source: Mapped[str] = mapped_column(
        choice("odometer_source", *ODOMETER_SOURCES), default="manual"
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, server_default=func.now())


class ServiceLog(Base):
    """One completed service. A combined filter job is two rows (engine + cabin)."""

    __tablename__ = "service_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(
        ForeignKey("vehicles.id", ondelete="CASCADE"), index=True
    )
    service_key: Mapped[str] = mapped_column(choice("service_key", *SERVICE_KEYS))
    service_date: Mapped[date]
    odometer_km: Mapped[Decimal | None] = mapped_column(Numeric(9, 1))
    confirmed: Mapped[bool] = mapped_column(default=True)  # only confirmed history anchors a rule
    oil_meets_spec: Mapped[bool | None]  # oil services only
    minder_reset_on: Mapped[
        date | None
    ]  # Honda Maintenance Minder reset linked to this service (R09)
    notes: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, server_default=func.now())
