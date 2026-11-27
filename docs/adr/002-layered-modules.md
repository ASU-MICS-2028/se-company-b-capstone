# ADR-002: Layered / light hexagonal structure per module

**Status:** Accepted · **Date:** 2026-11-24 · **Owner:** Eugene

## Context

The two pieces of real logic are the **reminder engine** (Germain, #44) and the **mechanic matching engine** (Isaac, #45). Their specs (the reminder rule spec and the mechanic matching spec, added to the repo in #41) are full of boundary cases (80%/100% thresholds, month clamping, 24 h freshness, Haversine radius equality) that need fast, isolated unit tests (RT-xx, MT-xx). The rules and ranking may change as the team validates them, and the engines are written by different people from the API.

## Decision

Each module uses the same layers:

```
router.py      HTTP only: parse request, call service, shape response (FastAPI)
schemas.py     Pydantic request/response models (the API contract)
service.py     use cases: orchestrates repositories and domain logic
repository.py  data access (SQLAlchemy), returns domain objects
models.py      SQLAlchemy tables
```

Domain logic lives in **pure Python** files that import neither FastAPI nor SQLAlchemy:

- `app/modules/reminders/engine.py`: takes a vehicle configuration, rules, service history, odometer readings and "now", and returns reminder states.
- `app/modules/mechanics/matching.py`: takes listings, an origin, a service, a radius and "now", and returns ranked `assessed` / `not_assessed` lists.

Dependencies point inward: router → service → (repository, engine). The engine depends on nothing.

## Consequences

- Germain and Isaac can write and test the engines with plain dataclasses and `pytest`, without a database or HTTP.
- The clock is a parameter, so the fixed `seed_reference_time` is easy to use in tests.
- There's more files per module than a single `routes.py`. Small modules may keep `service.py` thin.
- The service layer maps ORM rows to engine inputs, and that mapping needs its own API tests.

## Alternatives considered

- **Fat routers** (logic in route functions): fastest to write, but engine tests would need TestClient and a database, and the logic gets tangled with HTTP.
- **Full hexagonal** (ports and adapters for every dependency, interface classes): more ceremony than the team size and scope justify. We keep only the useful part, the pure domain core.
