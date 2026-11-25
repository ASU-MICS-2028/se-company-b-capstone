from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.core.types import Km

State = Literal["ok", "approaching", "overdue", "unknown"]
Trigger = Literal["time", "distance", "both", "dashboard", "n/a"]


class SourceOut(BaseModel):
    source_id: str = Field(examples=["S1"])
    title: str
    url: str


class LastService(BaseModel):
    service_date: date
    odometer_km: Km | None


class ReminderOut(BaseModel):
    """One card. Fields follow the rule spec evaluation contract, step 5 (US-05, US-06, US-07)."""

    rule_id: str | None = Field(examples=["R01"], description="null when no rule applies")
    service_key: str = Field(examples=["engine_oil_and_filter"])
    label: str = Field(examples=["Replace engine oil and filter"])
    state: State
    state_label: str = Field(examples=["Approaching"], description="Text, never colour alone")
    trigger: Trigger
    due_date: date | None
    due_odometer_km: Km | None = Field(description="Exact threshold, e.g. 56093.44")
    interval_months: int | None
    interval_km: Km | None
    last_service: LastService | None
    current_odometer_km: Km | None
    odometer_stale: bool = Field(description="Latest reading older than 30 days")
    missing_fields: list[str] = Field(examples=[["current_odometer"]])
    explanation: str
    sources: list[SourceOut]
    snoozed_until: date | None
    search_service: str | None = Field(
        examples=["oil_service"],
        description="Category for 'Find a mechanic'; null = no link (air-filter rules)",
    )
    help_link: Literal["manual", "mechanic_search"] | None = Field(
        description="Set when state is unknown (US-07)"
    )


class VehicleReminders(BaseModel):
    vehicle_id: int
    evaluated_on: date = Field(description="Local date, Africa/Accra")
    schedule: Literal["supported", "unknown"] = Field(
        description="`unknown` => show 'Schedule unknown' (US-07)"
    )
    reminders: list[ReminderOut]


class SnoozeIn(BaseModel):
    service_key: str
    until: date = Field(description="Max 30 days ahead (TODO confirm with A&E)")


class CompleteIn(BaseModel):
    """Mark done = log the service. Same validation as POST service-logs."""

    service_key: str
    service_date: date
    odometer_km: Km | None = Field(None, ge=0)
    confirm_lower: bool = False
    oil_meets_spec: bool | None = None
    minder_reset_on: date | None = None


class MinderPromptIn(BaseModel):
    """Driver reports an active Honda Maintenance Minder code (RT-15). Server sets reported_at."""

    code: str = Field(min_length=1, max_length=10, examples=["7"])


class MinderPromptOut(BaseModel):
    id: int
    code: str
    reported_at: datetime
    cleared_at: datetime | None
