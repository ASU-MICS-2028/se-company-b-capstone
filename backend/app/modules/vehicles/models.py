from datetime import datetime

from sqlalchemy import JSON, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, choice

# Value lists from data/seed/vehicles.json (G&I, Sprint 1).
POWERTRAINS = ("petrol", "diesel", "hybrid", "plug_in_hybrid", "electric")
DRIVING_CONDITIONS = ("normal", "primarily_dirt_or_dusty", "other_special_use", "unknown")
SOURCE_MARKETS = ("US", "CA", "GH", "OTHER", "UNKNOWN")
BODY_STYLES = ("sedan", "hatchback", "suv", "other", "unknown")


class VehicleModel(Base):
    """Curated catalogue row (vehicles.json). A hit helps data entry; it does not enable rules."""

    __tablename__ = "vehicle_models"

    catalogue_id: Mapped[str] = mapped_column(String(10), primary_key=True)  # "V03"
    make: Mapped[str] = mapped_column(String(40))
    model: Mapped[str] = mapped_column(String(40))
    year_from: Mapped[int]
    year_to: Mapped[int]
    powertrains: Mapped[list[str]] = mapped_column(JSON)
    rules_supported: Mapped[bool]
    note: Mapped[str | None]


class Vehicle(Base):
    """An owner's car. Catalogue link is optional so unlisted vehicles can be entered manually."""

    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    catalogue_id: Mapped[str | None] = mapped_column(ForeignKey("vehicle_models.catalogue_id"))
    make: Mapped[str] = mapped_column(String(40))
    model: Mapped[str] = mapped_column(String(40))
    model_year: Mapped[int]
    powertrain: Mapped[str] = mapped_column(choice("powertrain", *POWERTRAINS))
    body_style: Mapped[str] = mapped_column(choice("body_style", *BODY_STYLES), default="unknown")
    source_market: Mapped[str] = mapped_column(
        choice("source_market", *SOURCE_MARKETS), default="UNKNOWN"
    )
    driving_condition: Mapped[str] = mapped_column(
        choice("driving_condition", *DRIVING_CONDITIONS), default="unknown"
    )
    # Honda R10 condition, recorded separately from driving_condition. None = unknown.
    # TODO: confirm with G&I
    dusty_gravel_or_soot: Mapped[bool | None]
    # Toyota R01/R07 guard: previous oil met the guide spec. None = unknown -> normal oil rule off.
    last_oil_meets_spec: Mapped[bool | None]
    handbook_confirmed: Mapped[bool] = mapped_column(default=False)
    nickname: Mapped[str | None] = mapped_column(String(40))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
