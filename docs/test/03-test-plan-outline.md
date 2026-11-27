# Test plan outline
**Nkenten AutoCare · Sprint 1 · Germain and Isaac · 21 November 2026**

## Scope, environment and ownership

Cover registration and manual entry, service logging, explainable reminders, mechanic search and profiles, contact interactions, admin assessment and availability updates, and data access. Germain leads reminder cases and Isaac leads matching and quality checks. Proposed integration coordination with Eugene and front-end usability coordination with Alice and Elise are subject to team agreement. Use pytest for domain logic and FastAPI/SQLite integration with isolated databases. Use React Testing Library for accessible rendering and Playwright for the workflows. Pin fixture time and zone. Run unit and integration cases in CI once the app exists. Collect baseline performance and quality evidence separately.

## Reminder cases

| ID | Test | Expected |
|---|---|---|
| RT-01 | R01, 12,874 then 12,875 km elapsed, date well below 80% | OK then Approaching, calculated before display rounding |
| RT-02 | R01, 16,093 then 16,094 km elapsed, date under 80% | Approaching then Overdue by distance |
| RT-03 | R01, normal 12-month anniversary, low mileage | Overdue by time with due-today label |
| RT-04 | R02, primary dusty use, 8,046 then 8,047 km | Approaching then Overdue, R02 overrides R01 |
| RT-05 | R02 with 31 Aug 2026 history and low mileage | 28 Feb 2027 due date, exact day triggers |
| RT-06 | R02 with 31 Aug 2027 history | 29 Feb 2028 due date |
| RT-07 | R03 or R04 in known severe operation | Base schedule applies |
| RT-08 | R05/R08 under source-listed dust or heavy traffic | Unknown for the shortened interval with explanatory advice |
| RT-09 | R09 time fallback at 12 months, absent distance | Overdue by time if reset and oil service are confirmed |
| RT-10 | R10 at 24,000 km, no date threshold and both filters have confirmed history | Distance due for whichever filter reaches its own threshold |
| RT-11 | 2025 Camry hybrid vs 2025 Camry petrol. US Corolla sedan vs hatchback; Canada CR-V vs US CR-V | Only exact supported configuration and market activates |
| RT-12 | Manual-entry Almera, unknown market, or catalogue-only Corolla or CR-V | Unknown with manual or mechanic link |
| RT-13 | Missing service history, purchase date exists | Unknown. Purchase does not create a service |
| RT-14 | Odometer rollback, negative value, future date, stale current odometer or a current reading taken before service | Reject invalid edits. Legacy invalid values prompt correction. A reading older than 30 days or taken before service leaves distance unknown |
| RT-15 | R11 active Minder item 7 before 36 months, then no prompt at month 36 | Dashboard triggers due first. Time fallback triggers with confirmed history |
| RT-16 | Missing distance and 50%, 85%, then 100% time elapsed | Unknown, Approaching with missing field, Overdue |
| RT-17 | Toyota mile-input/metric equivalent and minute around midnight Africa/Accra | Same result across units, correct local date |
| RT-18 | Parse every seed, check source mappings, active intervals, unique matching and catalogue references | All references resolve. Missing/disjoint applicability is rejected |
| RT-19 | Unknown or nonrecommended Toyota oil grade, or special use without an exact rule | Unknown for normal oil. Exact supported special rule can still apply |
| RT-20 | R10 previous combined record, then only engine filter replaced | Cabin filter age and mileage baseline preserved |

## Matching and access cases

- **MT-01 through MT-10** reproduce the [matching fixture table](../rules/02-mechanic-matching-spec.md) at the fixed reference time.
- **MT-11** confirms Osu to East Legon is about 9.2 km. Check exact radius equality and just outside each of the two radius filters, including points that round to the same display distance.
- **MT-12** uses equal rounded distances. Newer valid update wins, then ascending ID. A null report sorts last.
- **MT-13** covers exactly 24 h, 24 h plus one second, a future timestamp, a missing report and stale unavailable. Availability is evaluated before filtering.
- **MT-14** checks a driver receives 404 for M08 and can never list it. An authenticated admin can access its admin record and see change history.
- **MT-15** exercises denied location permission, partial or conflicting origins, unknown neighbourhood, unsupported radius, and coordinates near bounds. Confirm search coordinates are absent from storage and logs.
- **MT-16** checks fixture profiles are limited to demo mode, have visible labels, and use a local contact simulation. Check that M01's assessment and diagnostics claim remain distinct on its profile.
- **AC-01–06** check authentication, cross-account vehicle isolation for reads and writes, admin-only status updates, hashed passwords, input validation, and account deletion/retention behavior per the agreed policy.
- **AT-US01-1 to AT-US04-3** are the browser acceptance cases for US-01, US-02 and US-04. See [acceptance cases](07-acceptance-cases.md).

## System, usability, and performance

Run the demo workflows end to end: register Ama’s supported Corolla, record a service, verify the sourced reminder, find brake mechanics in Osu, open a profile and run the demo contact action. Exercise a manual-entry vehicle and an assessment/availability change via admin. Verify readable states with keyboard and screen-reader semantics on a small mobile viewport.

With consent, plan a formative exercise with 5–8 drivers using registration, service logging and search. Record anonymised completion, median time to a suitable mechanic, error count and comments. Report sample size, recruitment, and limits. For performance, run 100 sequential calls for reminder and matching endpoints, then 10 concurrent clients for 60 seconds. Report p50/p95, error rate and environment, and compare to the provisional local p95 target of 500 ms. Run the separate 72 h quality measurement using the [metrics procedure](05-availability-reliability.md).

Entry requires a versioned app build, loaded fixtures, endpoints and health check. Before the planned 10 December demo, require passing critical assertions for reminders, matching, access, and all five workflows, with no unresolved critical defects. Run extended testing and measurement during 11–14 December. Record expected/actual result, build ID, evidence and defect ID. Track open issues and retests in GitHub. Any coverage target and latency target remain provisional until the team agrees on them. This outline records planned application tests. See [verification notes](06-steps-and-verification.md) for checks run on the sprint package.
