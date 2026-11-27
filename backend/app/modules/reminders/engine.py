"""Evaluate Corolla oil-and-filter reminders from an in-memory vehicle snapshot."""

from calendar import monthrange
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, replace
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

OIL_SERVICE = "engine_oil_and_filter"
MILES_TO_KM = Decimal("1.609344")
APPROACHING = Decimal("0.8")


@dataclass(frozen=True)
class Vehicle:
    catalogue_id: str | None
    make: str
    model: str
    model_year: int | None
    source_market: str
    powertrain: str
    body_style: str
    driving_condition: str
    handbook_confirmed: bool
    last_oil_meets_spec: bool | None
    odometer_replacement_unverified: bool = False


@dataclass(frozen=True)
class ServiceEvent:
    id: int
    service_key: str
    service_date: date | None
    odometer_km: Decimal | int | None
    confirmed: bool


@dataclass(frozen=True)
class OdometerReading:
    odometer_km: Decimal | int
    read_at: datetime | None


@dataclass(frozen=True)
class Reminder:
    state: str = "unknown"
    trigger: str = "n/a"
    rule_id: str | None = None
    source_ids: tuple[str, ...] = ()
    due_date: date | None = None
    due_odometer_km: Decimal | None = None
    last_service: ServiceEvent | None = None
    current_reading: OdometerReading | None = None
    missing_fields: tuple[str, ...] = ()
    explanation: str = ""


def _calendar_due(start: date, months: int) -> date:
    year_offset, month_index = divmod(start.month - 1 + months, 12)
    year, month = start.year + year_offset, month_index + 1
    return date(year, month, min(start.day, monthrange(year, month)[1]))


def _reading_date(reading: OdometerReading | None) -> date | None:
    if reading is None or reading.read_at is None:
        return None
    stamp = reading.read_at
    # Accra observes UTC year-round. SQLite can return a naive UTC timestamp.
    return (stamp.astimezone(UTC) if stamp.tzinfo else stamp).date()


def validate_service_readings(
    service: ServiceEvent,
    current_reading: OdometerReading | None,
    evaluated_on: date,
) -> None:
    """Raise ValueError for an inconsistent service/reading pair before accepting an edit."""
    baseline = service.odometer_km
    current = current_reading.odometer_km if current_reading else None
    for value in (baseline, current):
        if value is not None and (not Decimal(value).is_finite() or value < 0):
            raise ValueError("Correct the invalid odometer value.")
    if service.service_date and service.service_date > evaluated_on:
        raise ValueError("Correct the future oil-change date.")
    read_on = _reading_date(current_reading)
    if read_on is None:
        return
    if read_on > evaluated_on:
        raise ValueError("Correct the future odometer reading date.")
    if service.service_date and read_on < service.service_date:
        return  # An earlier reading is not evidence of rollback after the service.
    if baseline is not None and current is not None and current < baseline:
        raise ValueError("Check the odometer rollback against the oil-change record.")


def _matching_rules(vehicle: Vehicle, rules: Iterable[Mapping[str, Any]], condition: str):
    for rule in rules:
        if not (
            rule["verified"]
            and rule["make"] == vehicle.make == "Toyota"
            and rule["model"] == vehicle.model == "Corolla"
            and rule["service_type"] == OIL_SERVICE
            and rule["condition"] == condition
        ):
            continue
        for config in rule["applicability"]:
            if (
                config["catalogue_id"] == vehicle.catalogue_id
                and config["market"] == vehicle.source_market
                and config["powertrain"] == vehicle.powertrain
                and config["body_style"] == vehicle.body_style
                and vehicle.model_year is not None
                and config["year_from"] <= vehicle.model_year <= config["year_to"]
            ):
                yield rule, tuple(config["source_ids"])


def evaluate_corolla_oil(
    vehicle: Vehicle,
    rules: Iterable[Mapping[str, Any]],
    history: Iterable[ServiceEvent],
    current_reading: OdometerReading | None,
    evaluated_on: date,
) -> Reminder:
    """Evaluate one vehicle's history using the rules array from maintenance_rules.json.

    Distances are kilometres. evaluated_on is the Africa/Accra calendar date.
    Reading timestamps may carry an offset or be naive UTC as stored by SQLite.
    A confirmed undated service can anchor distance if it is the only candidate.
    """
    result = Reminder(current_reading=current_reading)
    if not vehicle.handbook_confirmed:
        return replace(
            result, missing_fields=("handbook_confirmed",), explanation="Confirm the handbook."
        )
    condition = vehicle.driving_condition
    if condition == "normal":
        if vehicle.last_oil_meets_spec is not True:
            return replace(
                result,
                missing_fields=("last_oil_meets_spec",)
                if vehicle.last_oil_meets_spec is None
                else (),
                explanation="The normal schedule requires confirmed use of the specified oil.",
            )
        condition = "normal_recommended_oil"
    elif condition != "primarily_dirt_or_dusty":
        return replace(
            result,
            missing_fields=("driving_condition",) if condition == "unknown" else (),
            explanation="Check the handbook for the applicable driving condition.",
        )

    matches = list(_matching_rules(vehicle, rules, condition))
    if not matches:
        fields = (
            "catalogue_id",
            "source_market",
            "body_style",
            "powertrain",
            "model_year",
            "make",
            "model",
        )
        missing = tuple(
            name for name in fields if getattr(vehicle, name) in (None, "", "unknown", "UNKNOWN")
        )
        return replace(
            result,
            missing_fields=missing,
            explanation="No verified Corolla oil schedule matches this configuration.",
        )
    if len(matches) != 1:
        raise ValueError("Overlapping Corolla oil rules for this configuration")
    rule, sources = matches[0]
    result = replace(result, rule_id=rule["rule_id"], source_ids=sources)

    events = [event for event in history if event.confirmed and event.service_key == OIL_SERVICE]
    if not events:
        return replace(
            result, missing_fields=("last_service",), explanation="Confirm an oil change."
        )
    if len(events) > 1 and any(event.service_date is None for event in events):
        return replace(
            result,
            missing_fields=("service_date",),
            explanation="Confirm which oil change was last.",
        )
    service = max(events, key=lambda event: (event.service_date or date.min, event.id))
    result = replace(result, last_service=service)
    if vehicle.odometer_replacement_unverified:
        return replace(
            result, explanation="Confirm the odometer replacement and corrected mileage."
        )
    try:
        validate_service_readings(service, current_reading, evaluated_on)
    except ValueError as error:
        return replace(result, explanation=str(error))
    start = service.service_date
    baseline = service.odometer_km

    missing = []
    ratios = {}
    due_date = None
    if start is None:
        missing.append("service_date")
    else:
        due_date = _calendar_due(start, rule["interval_months"])
        ratios["time"] = Decimal((evaluated_on - start).days) / (due_date - start).days

    due_km = None
    interval = Decimal(rule["source_miles"]) * MILES_TO_KM
    if baseline is None:
        missing.append("service_odometer_km")
    else:
        due_km = baseline + interval

    read_on = _reading_date(current_reading)
    if current_reading is None:
        missing.append("current_odometer")
    elif read_on is None:
        missing.append("read_at")
    elif (start and read_on < start) or (evaluated_on - read_on).days > 30:
        missing.append("current_odometer")
    elif baseline is not None:
        ratios["distance"] = Decimal(current_reading.odometer_km - baseline) / interval

    result = replace(
        result, due_date=due_date, due_odometer_km=due_km, missing_fields=tuple(missing)
    )
    for threshold, state in ((1, "overdue"), (APPROACHING, "approaching")):
        triggers = [dimension for dimension, ratio in ratios.items() if ratio >= threshold]
        if triggers:
            trigger = "both" if len(triggers) == 2 else triggers[0]
            message = f"Oil change {state} by {' and '.join(triggers)}."
            if due_date == evaluated_on:
                message += " Due today."
            if ratios.get("distance") == 1:
                message += " Due now."
            if missing:
                message += " Other threshold unknown."
            return replace(result, state=state, trigger=trigger, explanation=message)
    if missing:
        return replace(result, explanation="More service or odometer information is needed.")
    return replace(result, state="ok", explanation="Both thresholds are below 80%.")
