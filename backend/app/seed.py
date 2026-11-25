"""Seed loader: validate data/seed/*.json and load it into SQLite (#43).

    python -m app.seed [--dir PATH] [--db URL]

Order: catalogue -> sources -> categories, neighbourhoods -> rules -> (demo mode only) mechanics.
Idempotent: reference rows are upserted, so re-running never touches user data.
"""

import argparse
import json
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from sqlalchemy import Engine, create_engine, delete
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import create_all
from app.modules.mechanics.models import Mechanic, MechanicService, Neighbourhood, ServiceCategory
from app.modules.reminders.models import RULE_CONDITIONS, ReminderRule, RuleApplicability, Source
from app.modules.vehicles.models import VehicleModel

DEFAULT_DIR = Path(__file__).resolve().parents[2] / "data" / "seed"
MILES_TO_KM = Decimal("1.609344")
EXPECTED_THRESHOLDS = {"approaching_ratio": 0.8, "overdue_ratio": 1}


class SeedError(Exception):
    def __init__(self, problems: list[str]):
        super().__init__("\n".join(problems))
        self.problems = problems


def exact_km(rule: dict) -> Decimal | None:
    """Toyota miles are canonical (rule spec): 10,000 mi -> 16093.44 km, not the rounded 16,093."""
    if rule.get("source_miles"):
        return Decimal(rule["source_miles"]) * MILES_TO_KM
    return Decimal(str(rule["interval_km"])) if rule.get("interval_km") is not None else None


def validate(vehicles: dict, rules: dict, mechanics: dict, demo: bool = True) -> list[str]:
    """RT-18 import checks. Returns a list of problems (empty = OK)."""
    problems = []
    cats = {c["id"] for c in mechanics["service_categories"]}
    catalogue = {v["catalogue_id"] for v in vehicles["vehicles"]}
    sources = set(rules["sources"])
    retired = set(rules.get("retired_rule_ids", {}))

    if Decimal(str(rules["units"]["miles_to_km"])) != MILES_TO_KM:
        problems.append("units.miles_to_km must be 1.609344")
    if rules["state_thresholds"] != EXPECTED_THRESHOLDS:
        problems.append(f"state_thresholds must be {EXPECTED_THRESHOLDS} (engine constants)")

    seen_ids, configs = set(), []
    for r in rules["rules"]:
        rid = r["rule_id"]
        if rid in seen_ids:
            problems.append(f"{rid}: duplicate rule_id")
        if rid in retired:
            problems.append(f"{rid}: is retired")
        seen_ids.add(rid)
        if r["condition"] not in RULE_CONDITIONS:
            problems.append(f"{rid}: unknown condition {r['condition']}")
        if r.get("search_service") and r["search_service"] not in cats:
            problems.append(f"{rid}: unknown search_service {r['search_service']}")
        if r.get("interval_km") is None and r.get("interval_months") is None:
            problems.append(f"{rid}: needs interval_km or interval_months")
        km = exact_km(r)
        if r.get("source_miles") and r.get("interval_km") and round(km) != r["interval_km"]:
            problems.append(f"{rid}: interval_km {r['interval_km']} != round({km})")
        if not r["applicability"]:
            problems.append(f"{rid}: no applicability")
        for a in r["applicability"]:
            if a["catalogue_id"] not in catalogue:
                problems.append(f"{rid}: unknown catalogue_id {a['catalogue_id']}")
            for sid in a["source_ids"]:
                if sid not in sources:
                    problems.append(f"{rid}: unknown source {sid}")
            if a["year_from"] > a["year_to"]:
                problems.append(f"{rid}: year_from > year_to")
            configs.append((rid, r["service_type"], r["condition"], a))

    # Two rules for the same vehicle, service and condition must not cover the same configuration.
    def key(svc, cond, a):
        return (a["catalogue_id"], svc, cond, a["market"], a["powertrain"], a["body_style"])

    for i, (rid1, svc1, cond1, a1) in enumerate(configs):
        for rid2, svc2, cond2, a2 in configs[i + 1 :]:
            overlap = a1["year_from"] <= a2["year_to"] and a2["year_from"] <= a1["year_to"]
            if rid1 != rid2 and overlap and key(svc1, cond1, a1) == key(svc2, cond2, a2):
                problems.append(f"{rid1}/{rid2}: overlapping applicability for {svc1}/{cond1}")

    derived: dict[str, set[str]] = {c: set() for c in catalogue}
    for rid, _, _, a in configs:
        derived.setdefault(a["catalogue_id"], set()).add(rid)
    for v in vehicles["vehicles"]:
        if set(v.get("rule_ids", [])) != derived[v["catalogue_id"]]:
            problems.append(f"{v['catalogue_id']}: rule_ids disagree with rule applicability")
        if bool(derived[v["catalogue_id"]]) != v["rules_supported"]:
            problems.append(f"{v['catalogue_id']}: rules_supported disagrees with applicability")

    if demo:
        areas = {n["name"] for n in mechanics["neighbourhoods"]}
        for m in mechanics["mechanics"]:
            if m["neighbourhood"] not in areas:
                problems.append(f"{m['id']}: unknown neighbourhood {m['neighbourhood']}")
            for s in m["services"]:
                if s["category"] not in cats:
                    problems.append(f"{m['id']}: unknown service category {s['category']}")
            if m["assessment_status"] == "suspended" and m.get("published"):
                problems.append(f"{m['id']}: suspended listing must not be published")
    return problems


def _ts(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value.replace("Z", "+00:00")) if value else None


def _day(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def load(seed_dir: Path = DEFAULT_DIR, engine: Engine | None = None, demo: bool | None = None):
    """Validate everything first, then write in one transaction. Returns row counts."""
    from app.core.db import engine as default_engine

    engine = engine or default_engine
    demo = get_settings().demo_mode if demo is None else demo
    read = lambda name: json.loads((seed_dir / name).read_text(encoding="utf-8"))  # noqa: E731
    vehicles, rules = read("vehicles.json"), read("maintenance_rules.json")
    mechanics = read("mechanics.json")  # categories + neighbourhoods are always needed

    problems = validate(vehicles, rules, mechanics, demo)
    if problems:
        raise SeedError(problems)

    create_all(engine)
    counts = {}
    with Session(engine) as s, s.begin():
        for v in vehicles["vehicles"]:
            s.merge(VehicleModel(**{k: v[k] for k in v if k != "rule_ids"}))
        for sid, src in rules["sources"].items():
            s.merge(
                Source(
                    source_id=sid,
                    title=src["title"],
                    url=src["url"],
                    accessed=_day(src["accessed"]),
                )
            )
        for c in mechanics["service_categories"]:
            s.merge(ServiceCategory(**c))
        for n in mechanics["neighbourhoods"]:
            s.merge(Neighbourhood(**n))
        s.flush()
        s.execute(delete(RuleApplicability))  # rebuilt below; nothing user-owned points at it
        for r in rules["rules"]:
            rule = s.merge(
                ReminderRule(
                    **{k: r[k] for k in r if k not in ("applicability", "interval_km")},
                    interval_km=exact_km(r),
                )
            )
            for a in r["applicability"]:
                ap = RuleApplicability(**{k: a[k] for k in a if k != "source_ids"})
                ap.sources = [s.get(Source, sid) for sid in a["source_ids"]]
                rule.applicability.append(ap)
        counts.update(
            vehicle_models=len(vehicles["vehicles"]),
            rules=len(rules["rules"]),
            sources=len(rules["sources"]),
            service_categories=len(mechanics["service_categories"]),
            neighbourhoods=len(mechanics["neighbourhoods"]),
        )

        if demo:
            for m in mechanics["mechanics"]:
                fields = {k: m[k] for k in m if k != "services"}
                fields["assessed_on"] = _day(fields.get("assessed_on"))
                fields["availability_updated_at"] = _ts(fields.get("availability_updated_at"))
                mech = s.merge(Mechanic(**fields))
                mech.services = [
                    MechanicService(
                        category_id=x["category"],
                        verification=x["verification"],
                        assessed_on=mech.assessed_on if x["verification"] == "assessed" else None,
                        assessor=mech.assessor if x["verification"] == "assessed" else None,
                    )
                    for x in m["services"]
                ]
            counts.update(mechanics=len(mechanics["mechanics"]))
    return counts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dir", type=Path, default=DEFAULT_DIR)
    parser.add_argument("--db", help="Database URL (default: DATABASE_URL setting)")
    args = parser.parse_args(argv)
    if not (args.dir / "vehicles.json").exists():
        print(f"No seed files in {args.dir} (waiting on #41?)", file=sys.stderr)
        return 1
    try:
        counts = load(args.dir, create_engine(args.db) if args.db else None)
    except SeedError as e:
        print("Seed rejected:\n- " + "\n- ".join(e.problems), file=sys.stderr)
        return 1
    print("Seeded: " + ", ".join(f"{k}={v}" for k, v in counts.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
