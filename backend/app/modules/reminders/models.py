from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Column, ForeignKey, Numeric, String, Table, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, UTCDateTime, choice
from app.modules.vehicles.models import BODY_STYLES, POWERTRAINS, SOURCE_MARKETS

# Rule conditions in the seed; each selects an applicability Strategy (ADR-005).
RULE_CONDITIONS = (
    "base_schedule",
    "minder_fallback",
    "normal",
    "normal_recommended_oil",
    "primarily_dirt_or_dusty",
    "regular_dusty_gravel_or_visible_soot",
)

# Reminder *states* (OK / Approaching / Overdue / Unknown) are computed by engine.py on read,
# never stored. Only rules, their applicability and sources, and user snoozes are persisted.


class Source(Base):
    """Manufacturer document a rule threshold comes from (maintenance_rules.json `sources`)."""

    __tablename__ = "sources"

    source_id: Mapped[str] = mapped_column(String(10), primary_key=True)  # "S1"
    title: Mapped[str] = mapped_column(String(300))
    url: Mapped[str] = mapped_column(String(500))
    accessed: Mapped[date]


class ReminderRule(Base):
    __tablename__ = "reminder_rules"

    rule_id: Mapped[str] = mapped_column(String(10), primary_key=True)  # "R01"; R06 retired
    make: Mapped[str] = mapped_column(String(40))
    model: Mapped[str] = mapped_column(String(40))
    service_type: Mapped[str] = mapped_column(String(60))
    label: Mapped[str] = mapped_column(String(120))
    condition: Mapped[str] = mapped_column(choice("rule_condition", *RULE_CONDITIONS))
    source_miles: Mapped[int | None]  # canonical for Toyota; null for Honda
    # Exact km (source_miles * 1.609344 when miles are canonical). Null = dimension not used.
    interval_km: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    interval_months: Mapped[int | None]
    anchor: Mapped[str] = mapped_column(String(60))
    verified: Mapped[bool]
    # "Find a mechanic" category for this rule (matching spec, "Reminder to search mapping").
    # Null = no search link (air-filter rules until a category exists).
    search_service: Mapped[str | None] = mapped_column(ForeignKey("service_categories.id"))
    notes: Mapped[str | None] = mapped_column(String(500))

    applicability: Mapped[list["RuleApplicability"]] = relationship(
        back_populates="rule", cascade="all, delete-orphan"
    )


applicability_sources = Table(
    "rule_applicability_sources",
    Base.metadata,
    Column(
        "applicability_id",
        ForeignKey("rule_applicability.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("source_id", ForeignKey("sources.source_id"), primary_key=True),
)


class RuleApplicability(Base):
    """Exact configuration a rule covers. Only an exact match enables the rule."""

    __tablename__ = "rule_applicability"

    id: Mapped[int] = mapped_column(primary_key=True)
    rule_id: Mapped[str] = mapped_column(ForeignKey("reminder_rules.rule_id", ondelete="CASCADE"))
    catalogue_id: Mapped[str] = mapped_column(ForeignKey("vehicle_models.catalogue_id"))
    market: Mapped[str] = mapped_column(choice("source_market", *SOURCE_MARKETS))
    year_from: Mapped[int]
    year_to: Mapped[int]
    powertrain: Mapped[str] = mapped_column(choice("powertrain", *POWERTRAINS))
    body_style: Mapped[str] = mapped_column(choice("body_style", *BODY_STYLES))

    rule: Mapped[ReminderRule] = relationship(back_populates="applicability")
    sources: Mapped[list[Source]] = relationship(secondary=applicability_sources)


class ReminderSnooze(Base):
    __tablename__ = "reminder_snoozes"

    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(
        ForeignKey("vehicles.id", ondelete="CASCADE"), index=True
    )
    rule_id: Mapped[str] = mapped_column(ForeignKey("reminder_rules.rule_id"))
    service_key: Mapped[str] = mapped_column(String(40))  # R10 has two cards
    snoozed_until: Mapped[date]
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, server_default=func.now())


class MinderPrompt(Base):
    """Driver-reported Maintenance Minder prompt (Honda CR-V). The dashboard is authoritative:
    an active prompt makes its service due immediately (rule spec; RT-15).
    """

    __tablename__ = "minder_prompts"

    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(
        ForeignKey("vehicles.id", ondelete="CASCADE"), index=True
    )
    code: Mapped[str] = mapped_column(String(10))  # Minder code, e.g. "A", "0", "2", "7"
    reported_at: Mapped[datetime] = mapped_column(UTCDateTime)
    cleared_at: Mapped[datetime | None] = mapped_column(UTCDateTime)  # null = still active
