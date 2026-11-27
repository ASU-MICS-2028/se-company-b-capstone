from datetime import date, datetime

from sqlalchemy import Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, UTCDateTime, choice

ASSESSMENT_STATUSES = ("assessed", "pending", "self_reported", "suspended")
SERVICE_VERIFICATIONS = ("assessed", "self_reported", "pending")
AVAILABILITY_STATUSES = ("available", "busy", "unavailable")
COMPLAINT_STATUSES = ("open", "dismissed", "upheld")
# demo_dialog confirmed (G&I, #67); phone is the placeholder live option. TODO(A&E): decide.
CONTACT_MODES = ("demo_dialog", "phone")


class ServiceCategory(Base):
    """Searchable mechanic service (mechanics.json). ev_high_voltage is not searchable."""

    __tablename__ = "service_categories"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)  # "brake_service"
    label: Mapped[str] = mapped_column(String(80))
    searchable: Mapped[bool]
    note: Mapped[str | None] = mapped_column(String(300))


class Neighbourhood(Base):
    """Approximate neighbourhood centroid used as a search origin."""

    __tablename__ = "neighbourhoods"

    name: Mapped[str] = mapped_column(String(60), primary_key=True)
    lat: Mapped[float]
    lng: Mapped[float]


class Mechanic(Base):
    __tablename__ = "mechanics"

    id: Mapped[str] = mapped_column(String(10), primary_key=True)  # "M01"
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))  # future mechanic login
    name: Mapped[str] = mapped_column(String(120))
    is_demo: Mapped[bool] = mapped_column(default=False)
    published: Mapped[bool] = mapped_column(default=False)
    suspension_reason: Mapped[str | None] = mapped_column(String(300))
    neighbourhood: Mapped[str] = mapped_column(ForeignKey("neighbourhoods.name"))
    lat: Mapped[float]
    lng: Mapped[float]
    service_radius_km: Mapped[float] = mapped_column(Float)  # float maths in matching.py
    # Overall assessment
    assessment_status: Mapped[str] = mapped_column(
        choice("assessment_status", *ASSESSMENT_STATUSES)
    )
    assessed_on: Mapped[date | None]
    assessor: Mapped[str | None] = mapped_column(String(120))
    assessment_basis: Mapped[str | None] = mapped_column(String(500))
    # Last reported availability; freshness (24 h) is decided at query time by matching.py
    availability_status: Mapped[str | None] = mapped_column(
        choice("availability_status", *AVAILABILITY_STATUSES)
    )
    availability_updated_at: Mapped[datetime | None] = mapped_column(UTCDateTime)  # UTC
    contact_mode: Mapped[str] = mapped_column(choice("contact_mode", *CONTACT_MODES))
    test_purpose: Mapped[str | None] = mapped_column(String(300))  # fixture documentation only

    services: Mapped[list["MechanicService"]] = relationship(cascade="all, delete-orphan")


class MechanicService(Base):
    """Per-service verification: an assessed mechanic can still self-report one skill."""

    __tablename__ = "mechanic_services"

    mechanic_id: Mapped[str] = mapped_column(
        ForeignKey("mechanics.id", ondelete="CASCADE"), primary_key=True
    )
    category_id: Mapped[str] = mapped_column(ForeignKey("service_categories.id"), primary_key=True)
    verification: Mapped[str] = mapped_column(
        choice("service_verification", *SERVICE_VERIFICATIONS)
    )
    # US-12: required when verification == "assessed" (enforced in the admin service)
    assessor: Mapped[str | None] = mapped_column(String(120))
    assessed_on: Mapped[date | None]


class MechanicChange(Base):
    """Audit log of admin/mechanic edits to a listing (US-12, US-13, MT-14)."""

    __tablename__ = "mechanic_changes"

    id: Mapped[int] = mapped_column(primary_key=True)
    mechanic_id: Mapped[str] = mapped_column(ForeignKey("mechanics.id", ondelete="CASCADE"))
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    field: Mapped[str] = mapped_column(String(60))  # e.g. "services.brake_service.verification"
    old_value: Mapped[str | None] = mapped_column(String(500))
    new_value: Mapped[str | None] = mapped_column(String(500))
    changed_at: Mapped[datetime] = mapped_column(UTCDateTime, server_default=func.now())


class Complaint(Base):
    """Complaint about a mechanic, with the mechanic's response (US-14)."""

    __tablename__ = "complaints"

    id: Mapped[int] = mapped_column(primary_key=True)
    mechanic_id: Mapped[str] = mapped_column(ForeignKey("mechanics.id", ondelete="CASCADE"))
    recorded_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    description: Mapped[str] = mapped_column(String(2000))
    mechanic_response: Mapped[str | None] = mapped_column(String(2000))
    status: Mapped[str] = mapped_column(
        choice("complaint_status", *COMPLAINT_STATUSES), default="open"
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
