"""Seed loader checks (#43, RT-18) on a minimal fixture in the G&I seed format."""

import copy
import json
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.models import Mechanic, MechanicService, ReminderRule, RuleApplicability
from app.seed import SeedError, load, validate

APPLIES = {
    "catalogue_id": "V03",
    "market": "US",
    "year_from": 2025,
    "year_to": 2025,
    "powertrain": "petrol",
    "body_style": "sedan",
    "source_ids": ["S1"],
}
VEHICLES = {
    "vehicles": [
        {
            "catalogue_id": "V03",
            "make": "Toyota",
            "model": "Corolla",
            "year_from": 2023,
            "year_to": 2025,
            "powertrains": ["petrol"],
            "rules_supported": True,
            "note": None,
            "rule_ids": ["R01"],
        }
    ]
}
RULES = {
    "units": {"distance": "km", "time": "calendar months", "miles_to_km": 1.609344},
    "state_thresholds": {"approaching_ratio": 0.8, "overdue_ratio": 1},
    "sources": {
        "S1": {
            "title": "Toyota 2025 Corolla",
            "url": "https://example.com/s1",
            "accessed": "2026-11-21",
        }
    },
    "retired_rule_ids": {"R06": "retired"},
    "rules": [
        {
            "rule_id": "R01",
            "make": "Toyota",
            "model": "Corolla",
            "service_type": "engine_oil_and_filter",
            "label": "Replace engine oil",
            "condition": "normal_recommended_oil",
            "source_miles": 10000,
            "interval_km": 16093,
            "interval_months": 12,
            "applicability": [APPLIES],
            "anchor": "last_completed_service",
            "verified": True,
            "notes": None,
        }
    ],
}
MECHANICS = {
    "service_categories": [{"id": "brake_service", "label": "Brakes", "searchable": True}],
    "neighbourhoods": [{"name": "Osu", "lat": 5.556, "lng": -0.182}],
    "mechanics": [
        {
            "id": "M01",
            "is_demo": True,
            "name": "DEMO",
            "neighbourhood": "Osu",
            "lat": 5.556,
            "lng": -0.182,
            "service_radius_km": 10,
            "assessment_status": "assessed",
            "assessed_on": "2026-11-15",
            "assessor": "Demo assessor",
            "services": [{"category": "brake_service", "verification": "assessed"}],
            "availability_status": "available",
            "availability_updated_at": "2026-11-23T06:00:00Z",
            "contact_mode": "demo_dialog",
            "published": True,
        }
    ],
}


@pytest.fixture
def seed_dir(tmp_path):
    for name, data in [
        ("vehicles.json", VEHICLES),
        ("maintenance_rules.json", RULES),
        ("mechanics.json", MECHANICS),
    ]:
        (tmp_path / name).write_text(json.dumps(data))
    return tmp_path


@pytest.fixture
def engine(tmp_path):
    eng = create_engine(f"sqlite:///{tmp_path / 'seed.db'}")
    yield eng
    eng.dispose()


def count(engine, model):
    with Session(engine) as s:
        return s.scalar(select(func.count()).select_from(model))


def test_loads_and_is_idempotent(seed_dir, engine):
    for _ in range(2):
        assert load(seed_dir, engine, demo=True)["mechanics"] == 1
    assert count(engine, RuleApplicability) == 1
    assert count(engine, MechanicService) == 1
    with Session(engine) as s:
        assert s.get(ReminderRule, "R01").interval_km == Decimal("16093.44")  # exact, not 16093


def test_mechanics_only_in_demo_mode(seed_dir, engine):
    counts = load(seed_dir, engine, demo=False)
    assert "mechanics" not in counts
    assert counts["service_categories"] == 1  # reference data loads everywhere
    assert count(engine, Mechanic) == 0


def test_rule_search_link_is_stored(seed_dir, engine):
    rules = copy.deepcopy(RULES)
    rules["rules"][0]["search_service"] = "brake_service"
    (seed_dir / "maintenance_rules.json").write_text(json.dumps(rules))
    load(seed_dir, engine, demo=False)
    with Session(engine) as s:
        assert s.get(ReminderRule, "R01").search_service == "brake_service"


def broken(change):
    vehicles, rules, mechanics = copy.deepcopy((VEHICLES, RULES, MECHANICS))
    change(vehicles, rules, mechanics)
    return validate(vehicles, rules, mechanics)


@pytest.mark.parametrize(
    ("change", "expected"),
    [
        (
            lambda v, r, m: r["rules"][0]["applicability"][0].update(source_ids=["S9"]),
            "unknown source S9",
        ),
        (
            lambda v, r, m: r["rules"][0]["applicability"][0].update(catalogue_id="V99"),
            "unknown catalogue_id V99",
        ),
        (lambda v, r, m: r["rules"][0].update(rule_id="R06"), "is retired"),
        (lambda v, r, m: r["rules"][0].update(interval_km=16000), "interval_km 16000"),
        (lambda v, r, m: r["rules"].append({**r["rules"][0], "rule_id": "R99"}), "overlapping"),
        (lambda v, r, m: v["vehicles"][0].update(rule_ids=[]), "rule_ids disagree"),
        (
            lambda v, r, m: m["mechanics"][0].update(neighbourhood="Nkawkaw"),
            "unknown neighbourhood",
        ),
        (lambda v, r, m: r["rules"][0].update(condition="dusty"), "unknown condition"),
        (lambda v, r, m: r["rules"][0].update(search_service="oil"), "unknown search_service"),
    ],
    ids=[
        "source",
        "catalogue",
        "retired",
        "rounding",
        "overlap",
        "rule_ids",
        "neighbourhood",
        "condition",
        "search_service",
    ],
)
def test_validation_rejects(change, expected):
    assert any(expected in p for p in broken(change))


def test_rejected_seed_writes_nothing(seed_dir, engine):
    rules = copy.deepcopy(RULES)
    rules["rules"][0]["rule_id"] = "R06"
    (seed_dir / "maintenance_rules.json").write_text(json.dumps(rules))
    with pytest.raises(SeedError):
        load(seed_dir, engine, demo=True)
    assert not engine.dialect.has_table(engine.connect(), "reminder_rules")


def test_valid_fixture_has_no_problems():
    assert validate(VEHICLES, RULES, MECHANICS) == []


def test_turning_demo_mode_off_removes_demo_mechanics(seed_dir, engine):
    load(seed_dir, engine, demo=True)
    assert count(engine, Mechanic) == 1
    counts = load(seed_dir, engine, demo=False)
    assert counts["demo_mechanics_removed"] == 1
    assert count(engine, Mechanic) == count(engine, MechanicService) == 0
