# ADR-001: Modular monolith

**Status:** Accepted · **Date:** 2026-11-24 · **Owner:** Eugene

## Context

Six students, a six-week course, and an MVP of five screens (register vehicle, log service, reminders, mechanic search, mechanic profile) plus minimal admin. The proposal calls for a "modular client-server architecture" with separate rule-based reminder and matching modules. Nobody on the team runs production infrastructure, and the demo is on 10 December.

## Decision

Build the backend as **one FastAPI application, one process and one database**, split internally into modules: `auth`, `vehicles`, `service_logs`, `reminders`, `mechanics`. A module owns its tables and exposes behaviour through its service layer. Other modules call that service, never its repository or tables directly.

## Consequences

- One deploy, one log stream, one debugger session. Simple CI.
- Cross-module calls are plain function calls, so there's no network failure handling or API versioning between modules.
- Module boundaries are a convention, enforced in code review. Nothing stops an import shortcut, so reviewers must check for them.
- If one module later needs to scale or deploy separately (for example matching), its service interface is the seam to split along.

## Alternatives considered

- **Microservices** (one service per module): independent deploys and scaling we don't need, at the cost of service discovery, distributed debugging and several pipelines. Too much operational load for the team and timeline.
- **Serverless functions:** cold starts, vendor lock-in, and awkward with SQLite and local development. Harder to demo offline.
