"""Stub routes (contract v1). Real logic: reminders/engine.py (#44) + service layer."""

from datetime import UTC, date, datetime
from decimal import Decimal

from fastapi import APIRouter, status

from app.core.auth import BearerToken
from app.core.errors import ERRORS
from app.modules.reminders.schemas import (
    CompleteIn,
    LastService,
    MinderPromptIn,
    MinderPromptOut,
    ReminderOut,
    SnoozeIn,
    SourceOut,
    VehicleReminders,
)

router = APIRouter(prefix="/vehicles/{vehicle_id}/reminders", tags=["reminders"], responses=ERRORS)

_R01 = ReminderOut(
    rule_id="R01",
    service_key="engine_oil_and_filter",
    label="Replace engine oil and filter",
    state="approaching",
    state_label="Approaching",
    trigger="distance",
    due_date=date(2027, 6, 1),
    due_odometer_km=Decimal("56093.44"),
    interval_months=12,
    interval_km=Decimal("16093.44"),
    last_service=LastService(service_date=date(2026, 6, 1), odometer_km=Decimal("40000")),
    current_odometer_km=Decimal("53000"),
    odometer_stale=False,
    missing_fields=[],
    explanation="13,000 km of 16,093 km since your last oil change (81%). Due by 1 June 2027.",
    sources=[
        SourceOut(
            source_id="S1",
            title="Toyota 2025 Corolla maintenance guide",
            url="https://www.toyota.com/content/dam/toyota/brochures/pdf/2025/T-MMS-25Corolla.pdf",
        )
    ],
    snoozed_until=None,
    search_service="oil_service",
    help_link=None,
)
prompts = APIRouter(
    prefix="/vehicles/{vehicle_id}/minder-prompts", tags=["reminders"], responses=ERRORS
)
_PROMPT = MinderPromptOut(
    id=1, code="7", reported_at=datetime(2026, 11, 24, 8, tzinfo=UTC), cleared_at=None
)

_REMINDERS = VehicleReminders(
    vehicle_id=1, evaluated_on=date(2026, 11, 21), schedule="supported", reminders=[_R01]
)


@router.get("")
def list_reminders(vehicle_id: int, _: BearerToken) -> VehicleReminders:
    """Computed on read; nothing stored except snoozes."""
    return _REMINDERS


@router.post("/{rule_id}/snooze")
def snooze_reminder(vehicle_id: int, rule_id: str, body: SnoozeIn, _: BearerToken) -> ReminderOut:
    """404 if the rule does not apply to this vehicle. TODO(A&E): may overdue cards be snoozed?"""
    return _R01.model_copy(update={"snoozed_until": body.until})


@router.post("/{rule_id}/complete", status_code=status.HTTP_201_CREATED)
def complete_reminder(
    vehicle_id: int, rule_id: str, body: CompleteIn, _: BearerToken
) -> ReminderOut:
    """Logs the service and returns the re-evaluated card."""
    return _R01.model_copy(update={"state": "ok", "state_label": "Up to date"})


@prompts.get("")
def list_minder_prompts(vehicle_id: int, _: BearerToken) -> list[MinderPromptOut]:
    """Active and cleared prompts, newest first."""
    return [_PROMPT]


@prompts.post("", status_code=status.HTTP_201_CREATED)
def report_minder_prompt(vehicle_id: int, body: MinderPromptIn, _: BearerToken) -> MinderPromptOut:
    """RT-15. The dashboard is authoritative: the matching card becomes due now, trigger
    `dashboard`. 400 `not_a_minder_vehicle` for vehicles without Honda Minder rules."""
    return _PROMPT


@prompts.post("/{prompt_id}/clear")
def clear_minder_prompt(vehicle_id: int, prompt_id: int, _: BearerToken) -> MinderPromptOut:
    """Driver says the dashboard prompt is gone (e.g. after the service and a Minder reset)."""
    return _PROMPT.model_copy(update={"cleared_at": datetime(2026, 11, 25, 8, tzinfo=UTC)})
