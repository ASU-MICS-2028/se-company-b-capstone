# ADR-005: Design patterns in use

**Status:** Accepted · **Date:** 2026-11-24 · **Owner:** Eugene

## Context

The course assesses use of design patterns, and the team needs a shared vocabulary for code review. We only document patterns the code actually uses. When a pattern stops being used, update this ADR.

## Decision

### Repository (data access)

Each module's `repository.py` wraps SQLAlchemy queries behind methods such as `get_vehicle(owner_id, vehicle_id)` and `list_service_logs(vehicle_id)`. Services never build queries.
*Why:* keeps SQL in one place, makes the Postgres move cheap (ADR-003), and lets tests stub data access.

### Strategy (reminder rules and mechanic ranking)

- **Reminder rules:** each rule's `condition` (`normal_recommended_oil`, `primarily_dirt_or_dusty`, `base_schedule`, `minder_fallback`, `regular_dusty_gravel_or_visible_soot`, ...) selects an applicability check, and each rule's `anchor` (`last_completed_service`, `last_confirmed_oil_service_and_minder_reset`) selects how the start date is found. New conditions are added as new strategies, without changing the evaluator.
- **Mechanic ranking:** the sort key (distance rounded to 0.1 km, then newest valid report, then stable ID) is a single function passed to the matcher, so the team can swap it if user research changes priorities.

*Why:* G&I's specs are expected to evolve, and Strategy confines each change to one function plus its tests.

### Dependency Injection (FastAPI `Depends`)

Routes receive the DB session (`DbSession`), settings, the current user, and later the clock, through `Depends`. Tests swap them with `app.dependency_overrides`, for example a temp SQLite DB or a fixed clock at `seed_reference_time`.
*Why:* lets us test against an isolated database at a frozen time without monkeypatching.

## Consequences

- Reviewers can point at a named pattern ("this belongs in the repository").
- Strategy functions must stay pure so they can be unit-tested (ADR-002).

## Alternatives considered

- **Active Record** (models with query methods): less code, but mixes persistence into domain objects and makes the engines depend on SQLAlchemy.
- **A rules engine library or DSL:** too much for 10 rules, and harder for the team to read than plain functions.
