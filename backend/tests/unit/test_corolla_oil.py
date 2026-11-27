import json
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from app.modules.reminders.engine import (
    OIL_SERVICE,
    OdometerReading,
    ServiceEvent,
    Vehicle,
    evaluate_corolla_oil,
    validate_service_readings,
)

SEED = Path(__file__).resolve().parents[3] / "data" / "seed" / "maintenance_rules.json"
RULES = json.loads(SEED.read_text(encoding="utf-8"))["rules"]
CAR = Vehicle(
    catalogue_id="V03",
    make="Toyota",
    model="Corolla",
    model_year=2025,
    source_market="US",
    powertrain="petrol",
    body_style="sedan",
    driving_condition="normal",
    handbook_confirmed=True,
    last_oil_meets_spec=True,
)
SERVICE = ServiceEvent(1, OIL_SERVICE, date(2026, 6, 1), 40_000, confirmed=True)
NOW = datetime(2026, 11, 25, 9, tzinfo=UTC)
TODAY = NOW.date()


def evaluate(km, *, car=CAR, service=SERVICE, read_at=NOW, today=TODAY):
    reading = OdometerReading(km, read_at)
    return evaluate_corolla_oil(car, RULES, [service], reading, today)


@pytest.mark.parametrize(
    ("elapsed", "state"),
    [
        (12_874, "ok"),
        (12_875, "approaching"),
        (16_093, "approaching"),
        (16_094, "overdue"),
        (Decimal("12874.751"), "ok"),
        (Decimal("12874.752"), "approaching"),
        (Decimal("16093.43"), "approaching"),
        (Decimal("16093.44"), "overdue"),
    ],
)
def test_rt01_rt02_normal_oil_boundaries(elapsed, state):
    result = evaluate(40_000 + elapsed)
    assert (result.state, result.rule_id, result.source_ids) == (state, "R01", ("S1",))
    assert result.trigger == ("n/a" if state == "ok" else "distance")
    assert result.due_odometer_km == Decimal("56093.44")
    assert result.due_date == date(2027, 6, 1)
    assert result.missing_fields == ()


@pytest.mark.parametrize(
    ("km", "state", "trigger"),
    [
        (48_000, "unknown", "n/a"),
        (53_000, "approaching", "distance"),
        (56_094, "overdue", "distance"),
    ],
)
def test_unknown_service_date_still_uses_known_distance(km, state, trigger):
    result = evaluate(km, service=replace(SERVICE, service_date=None))
    assert (result.state, result.trigger, result.due_date) == (state, trigger, None)
    assert result.due_odometer_km == Decimal("56093.44")
    assert result.missing_fields == ("service_date",)


def test_rt03_anniversary():
    today = date(2027, 6, 1)
    reading = datetime(2027, 6, 1, tzinfo=UTC)
    previous_reading = reading - timedelta(days=1)
    previous = evaluate(40_100, today=previous_reading.date(), read_at=previous_reading)
    assert (previous.state, previous.trigger) == ("approaching", "time")
    result = evaluate(40_100, today=today, read_at=reading)
    assert (result.state, result.trigger) == ("overdue", "time")
    assert "Due today" in result.explanation
    both = evaluate(Decimal("56093.44"), today=today, read_at=reading)
    assert (both.state, both.trigger) == ("overdue", "both")


def test_missing_service_mileage_preserves_the_time_deadline():
    result = evaluate(
        60_000,
        service=replace(SERVICE, odometer_km=None),
        today=date(2027, 4, 1),
        read_at=datetime(2027, 4, 1, tzinfo=UTC),
    )
    assert (result.state, result.trigger) == ("approaching", "time")
    assert (result.due_date, result.due_odometer_km) == (date(2027, 6, 1), None)
    assert result.missing_fields == ("service_odometer_km",)


DUSTY = replace(CAR, driving_condition="primarily_dirt_or_dusty")


def test_rt04_dusty_use_overrides_normal_oil_interval():
    for km, state in [(48_046, "approaching"), (48_047, "overdue")]:
        result = evaluate(
            km, car=DUSTY, today=SERVICE.service_date, read_at=datetime(2026, 6, 1, tzinfo=UTC)
        )
        assert (result.rule_id, result.state, result.trigger) == ("R02", state, "distance")
        assert result.due_odometer_km == Decimal("48046.72")


@pytest.mark.parametrize(("year", "february_end"), [(2026, 28), (2027, 29)], ids=["RT-05", "RT-06"])
def test_dusty_oil_six_calendar_months(year, february_end):
    start = date(year, 8, 31)
    due = date(year + 1, 2, february_end)
    service = replace(SERVICE, service_date=start)
    for today, state in [(due - timedelta(days=1), "approaching"), (due, "overdue")]:
        reading = datetime.combine(today, NOW.timetz())
        result = evaluate(40_001, car=DUSTY, service=service, read_at=reading, today=today)
        assert (result.due_date, result.state, result.trigger) == (due, state, "time")


def test_rt13_vehicle_acquisition_does_not_start_the_service_clock():
    purchase_reading = OdometerReading(40_000, NOW)
    result = evaluate_corolla_oil(CAR, RULES, [], purchase_reading, TODAY)
    assert (result.state, result.trigger, result.missing_fields) == (
        "unknown",
        "n/a",
        ("last_service",),
    )
    assert result.due_date is None and result.due_odometer_km is None


def test_rt13_only_latest_confirmed_matching_service_can_anchor_the_rule():
    irrelevant = [replace(SERVICE, confirmed=False), replace(SERVICE, service_key="brake_fluid")]
    assert evaluate_corolla_oil(CAR, RULES, irrelevant, None, NOW.date()).state == "unknown"
    last = replace(SERVICE, id=4, odometer_km=50_000)
    older = replace(SERVICE, id=8, service_date=date(2025, 10, 1))
    history = [last, *irrelevant, SERVICE, older]
    reading = OdometerReading(50_100, NOW)
    result = evaluate_corolla_oil(CAR, RULES, history, reading, NOW.date())
    assert (result.state, result.due_odometer_km) == ("ok", Decimal("66093.44"))
    assert result == evaluate_corolla_oil(CAR, RULES, reversed(history), reading, NOW.date())


def test_ambiguous_undated_history_asks_which_service_was_last():
    history = [SERVICE, replace(SERVICE, id=2, service_date=None)]
    result = evaluate_corolla_oil(CAR, RULES, history, OdometerReading(60_000, NOW), NOW.date())
    assert (result.state, result.due_odometer_km) == ("unknown", None)
    assert "service_date" in result.missing_fields


@pytest.mark.parametrize("km", [-1, Decimal("NaN"), Decimal("Infinity"), 39_999])
def test_rt14_invalid_reading_requires_correction(km):
    with pytest.raises(ValueError, match="odometer"):
        validate_service_readings(SERVICE, OdometerReading(km, NOW), TODAY)
    result = evaluate(km)
    assert result.state == "unknown"
    assert "odometer" in result.explanation


def test_rt14_stale_or_pre_service_reading_only_disables_distance():
    fresh = evaluate(56_094, read_at=NOW - timedelta(days=30))
    assert fresh.state == "overdue"
    for read_at in [NOW - timedelta(days=31), datetime(2026, 5, 31, tzinfo=UTC)]:
        result = evaluate(40_000, read_at=read_at)
        assert (result.state, result.missing_fields) == ("unknown", ("current_odometer",))
    result = evaluate(56_094, read_at=NOW, today=date(2027, 6, 1))
    assert (result.state, result.trigger) == ("overdue", "time")


@pytest.mark.parametrize(
    ("service", "read_at"),
    [
        (replace(SERVICE, service_date=date(2027, 1, 1)), NOW),
        (SERVICE, NOW + timedelta(days=1)),
    ],
)
def test_rt14_future_service_or_reading_requires_correction(service, read_at):
    with pytest.raises(ValueError, match="future"):
        validate_service_readings(service, OdometerReading(48_000, read_at), TODAY)
    result = evaluate(48_000, service=service, read_at=read_at)
    assert result.state == "unknown" and "future" in result.explanation


def test_rt14_unverified_odometer_replacement_requests_correction():
    result = evaluate(56_094, car=replace(CAR, odometer_replacement_unverified=True))
    assert result.state == "unknown" and "odometer replacement" in result.explanation


@pytest.mark.parametrize(
    "change",
    [
        {"source_market": "GH"},
        {"model_year": 2022},
        {"body_style": "hatchback"},
        {"make": "Honda"},
        {"model": "Camry"},
        {"powertrain": "diesel"},
        {"catalogue_id": None},
        {"handbook_confirmed": False},
        {"last_oil_meets_spec": None},
        {"last_oil_meets_spec": False},
        {"driving_condition": "other_special_use"},
    ],
)
def test_unverified_or_inapplicable_configuration_returns_unknown(change):
    result = evaluate(60_000, car=replace(CAR, **change))
    assert (result.state, result.rule_id, result.due_date) == ("unknown", None, None)
