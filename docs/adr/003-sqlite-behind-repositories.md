# ADR-003: SQLite for the MVP, behind SQLAlchemy and repositories

**Status:** Accepted · **Date:** 2026-11-24 · **Owner:** Eugene

## Context

The proposal names "a relational SQLite prototype database" and says "a managed database may be considered for later deployment". Data volume is tiny: an 8-row catalogue, 10 rules, 10 demo mechanics, and a handful of demo users. Every developer and CI run needs a database with zero setup, and tests need a fresh isolated database per run.

## Decision

Use **SQLite** through **SQLAlchemy 2.x** ORM. All queries go through module repositories. The connection string comes from `DATABASE_URL` (pydantic-settings). Use only portable SQL types: decimals as `Numeric`, timestamps stored in UTC, enums as constrained strings. Don't use SQLite-only features.

## Consequences

- No database server to install. Tests use a temp file per test, and CI needs no services.
- SQLite has one writer at a time. That's fine for a demo, but not for real concurrent traffic.
- SQLite doesn't enforce `Numeric` precision or timezone-aware datetimes. The app layer must keep exact thresholds (for example 16,093.44 km) and store UTC.
- Foreign keys need `PRAGMA foreign_keys=ON` per connection, set in `app/core/db.py` (added with the schema, #10).
- Moving to Postgres means changing `DATABASE_URL`, adding a driver and adding migrations (Alembic). Repositories and engines don't change.

## Alternatives considered

- **Postgres from day one** (Docker or managed): production-like, but adds setup for six laptops and CI, which the MVP doesn't need.
- **JSON files / no database:** the seed is JSON already, but the MVP writes user data (vehicles, service logs) and needs relational integrity and per-user access control.
