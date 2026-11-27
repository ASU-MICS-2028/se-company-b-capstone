# Architecture (C4)

Diagrams use Mermaid C4 syntax so they render on GitHub. Decisions behind them are in [../adr/](../adr/).

## Level 1: System context

```mermaid
C4Context
  title Nkenten AutoCare: system context

  Person(driver, "Driver (Ama)", "Car owner. Registers vehicles, logs services, sees reminders, searches mechanics.")
  Person(mechanic, "Mechanic (Kojo)", "Garage or roadside mechanic. Listed with assessed and self-reported services.")
  Person(admin, "Nkenten admin", "Reviews listings, updates assessment and availability, handles complaints.")

  System(autocare, "Nkenten AutoCare", "Service history, explainable maintenance reminders, assessed mechanic search.")

  System_Ext(manuals, "Manufacturer maintenance guides", "Toyota US and Honda Canada schedules. Curated into the rule seed, not called at runtime.")
  System_Ext(geo, "Browser geolocation", "Optional, consent-based device location.")
  System_Ext(sms, "SMS / WhatsApp gateway (future)", "Reminder notifications and mechanic contact. Not in MVP.")
  System_Ext(maps, "Maps / geocoding service (future)", "Map view and address lookup. MVP uses a fixed neighbourhood list.")

  Rel(driver, autocare, "Uses", "HTTPS, browser")
  Rel(admin, autocare, "Administers", "HTTPS, browser")
  Rel(mechanic, autocare, "Is listed in; contacted via demo dialog", "")
  Rel(autocare, geo, "Requests location after user action", "Browser API")
  Rel(manuals, autocare, "Thresholds and sources, curated by G&I", "Seed JSON")
  Rel(autocare, sms, "Sends reminders (future)", "HTTPS API")
  Rel(autocare, maps, "Geocodes, shows maps (future)", "HTTPS API")
```

AutoCare is a single system used through the browser by **drivers** (persona Ama) and **admins**. **Mechanics** (persona Kojo) are listed in the system. In the MVP they don't log in: admins maintain their assessment and availability, and drivers "contact" fictional demo mechanics through a local dialog, with no real phone numbers. Maintenance thresholds come from **manufacturer guides**, but G&I curate them into `maintenance_rules.json`. The app never fetches them live. Location is either a named neighbourhood or a one-off **browser geolocation** reading, kept in memory only. SMS/WhatsApp notifications and a maps provider are marked *future* and are outside the MVP scope.

## Level 2: Containers

```mermaid
C4Container
  title Nkenten AutoCare: containers

  Person(driver, "Driver (Ama)")
  Person(admin, "Nkenten admin")

  System_Boundary(autocare, "Nkenten AutoCare") {
    Container(spa, "Web app (SPA)", "React, Vite, TypeScript", "Five MVP screens plus admin tables. Mobile-first, accessible labels.")
    Container(api, "API", "Python 3.12, FastAPI, SQLAlchemy", "Modules: auth, vehicles, service_logs, reminders (rule engine), mechanics (matching engine), admin")
    ContainerDb(db, "Database", "SQLite file", "Users, vehicles, odometer readings, service logs, catalogue, rules, sources, mechanics, assessments")
    Container(seed, "Seed loader", "Python CLI (make seed)", "Validates and imports data/seed JSON")
  }

  Rel(driver, spa, "Uses", "HTTPS")
  Rel(admin, spa, "Uses", "HTTPS")
  Rel(spa, api, "Calls /api/v1/*", "HTTPS, JSON, bearer token")
  Rel(api, db, "Reads and writes", "SQLAlchemy, SQL")
  Rel(seed, db, "Inserts catalogue, rules, mechanics", "SQLAlchemy, SQL")
```

The **SPA** is static files. In development Vite serves them and proxies `/api` to the API; in hosted environments nginx does the same (ADR-004). Every interaction is a JSON call to the **API**, a modular monolith (ADR-001) whose modules follow router → service → repository, with the two engines kept as pure Python (ADR-002). The **reminder engine** evaluates rules against service history and odometer readings on each request. Reminder states are computed, not stored. The **matching engine** filters and ranks mechanics from one snapshot. The **SQLite** database (ADR-003) is created and filled by the **seed loader**. It loads vehicles, then rules, then mechanics, and loads mechanics only in demo and test environments.

## Deployment view

```mermaid
flowchart TB
  subgraph laptop["Dev: each laptop"]
    vite["Vite dev server :5173"] -->|proxy /api| uv["uvicorn --reload :8000"]
    uv --> sqlite1[("autocare.db + seed")]
  end
  subgraph stg["Staging: host TBD (ADR-004)"]
    nginx1["autocare-web (nginx + built SPA)"] -->|/api| api1["autocare-api container"]
    api1 --> sqlite2[("SQLite on volume, re-seeded on deploy")]
  end
  subgraph prd["Production: host TBD (ADR-004)"]
    nginx2["autocare-web"] -->|/api| api2["autocare-api"]
    api2 --> sqlite3[("SQLite on volume, demo data")]
  end
  gh["GitHub Actions + GHCR"] -->|push to staging| stg
  gh -->|tag vX.Y.Z on main, approval| prd
```

Three environments run the same code. **Dev** runs natively (or in Docker, if we adopt the bind-mounted setup) with a local SQLite file. **Staging** and **production** run the same two container images, built once in GitHub Actions and stored in GHCR. They differ only in environment variables and secrets. Staging is redeployed and re-seeded on every push to `staging`. Production only changes when a release tag on `main` is approved. Hosting is still *proposed* in ADR-004. See [../devops.md](../devops.md).
