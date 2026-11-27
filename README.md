# Nkenten AutoCare

[![Backend CI](https://github.com/ASU-MICS-2028/se-company-b-capstone/actions/workflows/ci-backend.yml/badge.svg?branch=dev)](https://github.com/ASU-MICS-2028/se-company-b-capstone/actions/workflows/ci-backend.yml)
[![Frontend CI](https://github.com/ASU-MICS-2028/se-company-b-capstone/actions/workflows/ci-frontend.yml/badge.svg?branch=dev)](https://github.com/ASU-MICS-2028/se-company-b-capstone/actions/workflows/ci-frontend.yml)

A mobile-friendly web app for Ghanaian car owners to keep a vehicle service history, get explainable maintenance reminders, and find nearby assessed mechanics.
ICS 530 Software Engineering Essentials team project by Nkenten Technologies.

MVP vehicles: Toyota Corolla, Toyota Camry, Honda CR-V (other vehicles can be entered manually).
MVP screens: register vehicle, log service, reminder view, mechanic search, mechanic profile.

## Team and lanes

| Member | Lane |
|---|---|
| Henry | Scrum Master: check-ins, sprint planning, board and backlog |
| Eugene | Architecture, data, repo and DevOps |
| Alice & Elise | Personas, user stories and acceptance criteria, wireframes, requirements |
| Germain & Isaac | Reminder rule spec, mechanic matching spec, seed data, test plan, risk register, availability/reliability formulas |

## Stack

- **Backend:** FastAPI (Python 3.11+), SQLAlchemy 2.x, Pydantic v2, SQLite
- **Frontend:** React + Vite + TypeScript
- **Tooling:** ruff, pytest, pytest-bdd, pytest-cov; ESLint, Vitest, React Testing Library

## Run locally

Prerequisites: Python 3.11+ (the Makefile uses `python3.12`; override with `make PYTHON=python3.11 ...`), Node 20+, npm.

```bash
make dev-backend    # creates backend/.venv on first run, serves http://localhost:8000 (Swagger at /docs)
make dev-frontend   # installs node_modules on first run, serves http://localhost:5173
```

Open http://localhost:5173. The home page shows the API health check. The Vite dev server proxies `/api` to the backend.

Other targets:

```bash
make test   # backend pytest (skips @pending) + frontend Vitest
make lint   # ruff + ESLint + TypeScript type-check
make seed   # create the SQLite DB and load data/seed (safe to re-run)
```

Backend config comes from environment variables. See [backend/.env.example](backend/.env.example).

## How we work

Branching (`main` ← `staging` ← `dev` ← `feat/<issue>-...`), conventional commits, PR rules and review: see [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md).

## Docs

| Doc | Status |
|---|---|
| [Contributing and branching](docs/CONTRIBUTING.md) | ✅ |
| [DevOps: environments and pipeline](docs/devops.md) | ✅ |
| [Architecture decisions (ADRs)](docs/adr/) | ✅ |
| [C4 diagrams and deployment view](docs/architecture/) | ✅ |
| [Data schema (ER diagram)](docs/data/schema.md) | ✅ |
| [API contract v1](docs/api/) | Sprint 1, in progress |
| [Testing strategy](docs/testing.md) | Sprint 1, in progress |
| [Intelligence and quality package (index)](docs/README.md) | ✅ Sprint 1 |
| [Reminder rule spec](docs/rules/01-reminder-rule-spec.md) | ✅ Sprint 1 |
| [Mechanic matching spec](docs/rules/02-mechanic-matching-spec.md) | ✅ Sprint 1 |
| [Test plan outline](docs/test/03-test-plan-outline.md) | ✅ Sprint 1 |
| [Availability and reliability formulas](docs/test/05-availability-reliability.md) | ✅ Sprint 1 |
| [Risk register v1](docs/risk/04-risk-register-v1.md) ([CSV](docs/risk/risk-register-v1.csv)) | ✅ Sprint 1 |
| [Seed data: vehicles, rules, mechanics](data/seed/) | ✅ Sprint 1 |
| [Source material](docs/source/) | Brief and proposal |

## Repo layout

```
backend/   FastAPI app (app/core, app/modules/<module>) and tests (unit, api, acceptance)
frontend/  React + Vite SPA
docs/      architecture, adr, api, data, source
data/seed/ JSON seed files
.github/   CI workflows, issue and PR templates
```
