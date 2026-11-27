# API contract v1

**Status:** draft for team review (#11). Auth is implemented (#49). · **Base path:** `/api/v1` · **Live spec:** Swagger at http://localhost:8000/docs (OpenAPI at `/openapi.json`)

Apart from auth, every route below exists in the backend as a **stub** with real request/response schemas that returns example data. Real logic lands in the issue named per endpoint. Frontend work (#51) can build against the stubs now. The Pydantic schemas in `backend/app/modules/*/schemas.py` are the source of truth; if this page and Swagger disagree, Swagger wins and this page gets fixed.

## Conventions

- **JSON**, `snake_case` keys, UTF-8.
- **Dates** ISO 8601: `date` = `YYYY-MM-DD`; `datetime` = UTC with offset (`2026-11-23T06:00:00Z`). Datetimes sent without an offset are rejected. The reminder engine evaluates calendar dates in `Africa/Accra`.
- **Distance** in kilometres. Decimals are JSON numbers; exact thresholds keep their fraction (`16093.44`).
- **Auth:** `Authorization: Bearer <token>` from `/auth/login` or `/auth/register`. Roles: `driver`, `mechanic`, `admin`. Auth endpoints are real (#49). The other routes are still stubs that accept the header without checking it, and each gets `CurrentUser` / `require_role(...)` when its logic lands.
- **Ownership:** a driver only ever sees their own vehicles. Another user's vehicle returns **404**, not 403, so IDs don't leak.
- **Pagination** on growing lists: `?page=1&page_size=20` (max 100). Response:

  ```json
  {"items": [], "page": 1, "page_size": 20, "total": 0}
  ```

- **Errors** always use one shape:

  ```json
  {"error": {"code": "unknown_neighbourhood", "message": "Neighbourhood not supported", "details": {"suggestions": ["Osu", "Labone"]}}}
  ```

  | Status | `code` | When |
  |---|---|---|
  | 400 | domain code, e.g. `unsupported_service`, `unknown_neighbourhood`, `future_date`, `unknown_catalogue_id` | well-formed request the domain rejects |
  | 401 | `unauthorized`, `invalid_credentials` | missing/invalid token, bad login |
  | 403 | `forbidden` | wrong role |
  | 404 | `not_found` | missing, not yours, suspended or hidden |
  | 409 | `account_exists`, `odometer_lower_than_latest` | conflicts with stored state |
  | 422 | `validation_error` (`details` = list of `{loc, msg}`) | malformed input |

- **Enums** (from G&I's seed): powertrain `petrol|diesel|hybrid|plug_in_hybrid|electric`; body style `sedan|hatchback|suv|other|unknown`; source market `US|CA|GH|OTHER|UNKNOWN`; driving condition `normal|primarily_dirt_or_dusty|other_special_use|unknown`; reminder state `ok|approaching|overdue|unknown`; availability `available|busy|unavailable|unknown`; verification `assessed|self_reported|pending`.

## Endpoint index

| Method | Path | Purpose | Auth | Story · screen |
|---|---|---|---|---|
| `POST` | `/api/v1/auth/register` | Register | none | US-01 · Sign up |
| `POST` | `/api/v1/auth/login` | Log in | none | US-01 |
| `GET` | `/api/v1/auth/me` | Current user | any | all screens |
| `GET` | `/api/v1/vehicle-models` | List catalogue | none | US-02 · Register vehicle |
| `GET` | `/api/v1/vehicles` | List my vehicles | driver | US-01 (empty garage), US-02 |
| `POST` | `/api/v1/vehicles` | Register vehicle | driver | US-02, US-03 · Register vehicle |
| `GET` | `/api/v1/vehicles/{vehicle_id}` | Get vehicle | owner | US-02 |
| `PATCH` | `/api/v1/vehicles/{vehicle_id}` | Update vehicle | owner | US-02 |
| `DELETE` | `/api/v1/vehicles/{vehicle_id}` | Delete vehicle | owner | AC-06 |
| `GET` | `/api/v1/vehicles/{vehicle_id}/service-logs` | Service history | owner | US-04 · Log service |
| `POST` | `/api/v1/vehicles/{vehicle_id}/service-logs` | Log service | owner | US-04 · Log service |
| `GET` | `/api/v1/vehicles/{vehicle_id}/odometer-readings` | Odometer history | owner | US-02 |
| `POST` | `/api/v1/vehicles/{vehicle_id}/odometer-readings` | Record odometer | owner | US-02, US-05 |
| `GET` | `/api/v1/vehicles/{vehicle_id}/reminders` | Reminder view | owner | US-05, US-06, US-07 · Reminder view |
| `POST` | `/api/v1/vehicles/{vehicle_id}/reminders/{rule_id}/snooze` | Snooze | owner | Reminder view |
| `POST` | `/api/v1/vehicles/{vehicle_id}/reminders/{rule_id}/complete` | Mark done | owner | US-04, US-05 |
| `GET` | `/api/v1/vehicles/{vehicle_id}/minder-prompts` | List Minder prompts | owner | RT-15 · Reminder view |
| `POST` | `/api/v1/vehicles/{vehicle_id}/minder-prompts` | Report Minder prompt | owner | RT-15 · Reminder view |
| `POST` | `/api/v1/vehicles/{vehicle_id}/minder-prompts/{prompt_id}/clear` | Clear Minder prompt | owner | RT-15 |
| `GET` | `/api/v1/service-categories` | Service list | none | US-08 · Mechanic search |
| `GET` | `/api/v1/neighbourhoods` | Neighbourhood list | none | US-08, US-09 |
| `GET` | `/api/v1/mechanics/search` | Search | none | US-08, US-09, US-10 · Mechanic search |
| `GET` | `/api/v1/mechanics/{mechanic_id}` | Mechanic profile | none | US-11 · Mechanic profile |
| `PUT` | `/api/v1/mechanics/{mechanic_id}/availability` | Report availability | mechanic (own) or admin | US-13 |
| `GET` | `/api/v1/admin/mechanics` | List listings | admin | Admin: review |
| `GET` | `/api/v1/admin/mechanics/{mechanic_id}` | Listing detail | admin | MT-14 |
| `PUT` | `/api/v1/admin/mechanics/{mechanic_id}/assessment` | Update assessment | admin | US-12, US-14 · Admin: review |
| `GET` | `/api/v1/admin/mechanics/{mechanic_id}/complaints` | List complaints | admin | US-14 · Admin: complaints |
| `POST` | `/api/v1/admin/mechanics/{mechanic_id}/complaints` | Record complaint | admin | US-14 |
| `PATCH` | `/api/v1/admin/complaints/{complaint_id}` | Respond / resolve | admin | US-14 |

## Seed fields → API (#35)

| Seed field | Exposed as |
|---|---|
| rule `applicability[]` (market, years, powertrain, body style) | Matched against `VehicleIn` `source_market`, `model_year`, `powertrain`, `body_style`; result shown as `VehicleOut.reminder_support` and `VehicleReminders.schedule` |
| rule `source_miles`, `interval_km`, `interval_months` (nullable) | `ReminderOut.interval_km` (exact), `interval_months`; null = dimension not used |
| rule sources | `ReminderOut.sources[]` |
| `condition_input_note` inputs | `VehicleIn.driving_condition`, `regular_dusty_gravel_or_visible_soot` (Honda R10), `last_oil_meets_spec`; `ServiceLogIn.oil_meets_spec`, `minder_reset_on` |
| rule `search_service` (matching spec, "Reminder to search mapping") | `ReminderOut.search_service`, used as `service` for `/mechanics/search`; null = no "Find a mechanic" action |
| Dashboard prompts (rule spec, RT-15) | `/vehicles/{vehicle_id}/minder-prompts` |
| mechanic `services[].verification` | `SearchResult.service_verification`; profile `assessed_services` vs `other_services` |
| `service_radius_km` | `MechanicProfile.service_radius_km` (filtering happens server-side) |
| `availability_status`, `availability_updated_at` | `AvailabilityOut` (`status` effective after the 24 h rule, `reported_status`, `reported_at`) |
| `assessment_status`, `assessed_on`, `assessor`, `assessment_basis` | Profile and admin listing |
| `suspension_reason`, `published` | Admin listing only; drivers get 404 |
| `is_demo`, `contact_mode` | `SearchResult.is_demo`, `MechanicProfile.contact` (demo dialog, never a phone number) |
| `lat`/`lng`, neighbourhood centroids | Not exposed; only `distance_km` |
| `test_purpose`, `seed_reference_time` | Not exposed (fixture/test only) |

## Open questions

- **Odometer rollback:** US-04 says "ask to confirm"; the rule spec says reject through the normal write path. The contract follows US-04 (`409` unless `confirm_lower: true`) and the engine treats confirmed-lower history as needing correction. *A&E + G&I to agree.*
- **Air-filter search links:** R05, R08 and R10 have no `search_service` until a matching category exists. *Germain to confirm.*
- **Snooze rules:** maximum length, and whether overdue cards can be snoozed. *A&E.*
- **Phone format:** international (`+233…`) required for sign-up; spaces, dashes and brackets are stripped. *A&E to confirm.*

## Auth

### POST `/api/v1/auth/register` — Register

- **Purpose:** Create a **driver** account with email **or** phone (spaces in the phone are ignored) and log in. A `role` in the body is ignored; admins and mechanics are created with `python -m app.modules.auth.cli`.
- **Auth:** none
- **Supports:** US-01 · Sign up
- **Implemented in:** #49 (done)
- **Success:** `201`
- **Errors:** 422 `validation_error` (neither email nor phone, non-international phone, password under 8, blank name) · 409 `account_exists` ("An account with this email exists" / "...phone number exists")

Request:

```json
{
  "full_name": "Ama Mensah",
  "email": "ama@example.com",
  "phone": "+233 20 123 4567",
  "password": "Demo-pass-2026"
}
```

Response:

```json
{
  "access_token": "eyJzdWIiOjEsInJvbGUiOiJkcml2ZXIi...signature",
  "token_type": "bearer",
  "expires_in": 43200,
  "user": {
    "id": 1,
    "full_name": "Ama Mensah",
    "email": "ama@example.com",
    "phone": "+233201234567",
    "role": "driver"
  }
}
```

### POST `/api/v1/auth/login` — Log in

- **Purpose:** Exchange email-or-phone + password for a bearer token (`expires_in` seconds, default 12 h).
- **Auth:** none
- **Supports:** US-01
- **Implemented in:** #49 (done)
- **Success:** `200`
- **Errors:** 401 `invalid_credentials` (same message for unknown login and wrong password)

Request:

```json
{
  "login": "ama@example.com",
  "password": "Demo-pass-2026"
}
```

Response:

```json
{
  "access_token": "eyJzdWIiOjEsInJvbGUiOiJkcml2ZXIi...signature",
  "token_type": "bearer",
  "expires_in": 43200,
  "user": {
    "id": 1,
    "full_name": "Ama Mensah",
    "email": "ama@example.com",
    "phone": "+233201234567",
    "role": "driver"
  }
}
```

### GET `/api/v1/auth/me` — Current user

- **Purpose:** Who am I, and which role.
- **Auth:** any
- **Supports:** all screens
- **Implemented in:** #49 (done)
- **Success:** `200`
- **Errors:** 401 `unauthorized` (missing, invalid or expired token)

Response:

```json
{
  "id": 1,
  "full_name": "Ama Mensah",
  "email": "ama@example.com",
  "phone": "+233201234567",
  "role": "driver"
}
```


## Vehicle catalogue

### GET `/api/v1/vehicle-models` — List catalogue

- **Purpose:** Picker for register-vehicle. Optional `make`, `model` filters. Not paginated (8 rows).
- **Auth:** none
- **Supports:** US-02 · Register vehicle
- **Implemented in:** #50
- **Success:** `200`
- **Errors:** —

Response:

```json
[
  {
    "catalogue_id": "V03",
    "make": "Toyota",
    "model": "Corolla",
    "year_from": 2023,
    "year_to": 2025,
    "powertrains": [
      "petrol",
      "hybrid"
    ],
    "rules_supported": true,
    "note": null
  }
]
```


## Vehicles

### GET `/api/v1/vehicles` — List my vehicles

- **Purpose:** Caller's own vehicles only. Paginated.
- **Auth:** driver
- **Supports:** US-01 (empty garage), US-02
- **Implemented in:** #50
- **Success:** `200`
- **Errors:** 401

Response:

```json
{
  "items": [
    {
      "id": 1,
      "catalogue_id": "V03",
      "make": "Toyota",
      "model": "Corolla",
      "model_year": 2025,
      "powertrain": "petrol",
      "body_style": "sedan",
      "source_market": "US",
      "driving_condition": "normal",
      "regular_dusty_gravel_or_visible_soot": null,
      "last_oil_meets_spec": true,
      "handbook_confirmed": true,
      "nickname": null,
      "reminder_support": "supported",
      "latest_odometer_km": 48000.0,
      "latest_odometer_at": "2026-11-21T09:00:00Z"
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 1
}
```

### POST `/api/v1/vehicles` — Register vehicle

- **Purpose:** Create a vehicle and its first odometer reading. Omit `catalogue_id` for manual entry; response `reminder_support: limited` drives the "reminders may be limited" message.
- **Auth:** driver
- **Supports:** US-02, US-03 · Register vehicle
- **Implemented in:** #50
- **Success:** `201`
- **Errors:** 422 (negative/blank odometer, bad enum) · 400 `unknown_catalogue_id`

Request:

```json
{
  "make": "Toyota",
  "model": "Corolla",
  "model_year": 2025,
  "powertrain": "petrol",
  "odometer_km": 48000
}
```

Response:

```json
{
  "id": 1,
  "catalogue_id": "V03",
  "make": "Toyota",
  "model": "Corolla",
  "model_year": 2025,
  "powertrain": "petrol",
  "body_style": "sedan",
  "source_market": "US",
  "driving_condition": "normal",
  "regular_dusty_gravel_or_visible_soot": null,
  "last_oil_meets_spec": true,
  "handbook_confirmed": true,
  "nickname": null,
  "reminder_support": "supported",
  "latest_odometer_km": 48000.0,
  "latest_odometer_at": "2026-11-21T09:00:00Z"
}
```

### GET `/api/v1/vehicles/{vehicle_id}` — Get vehicle

- **Purpose:** One vehicle.
- **Auth:** owner
- **Supports:** US-02
- **Implemented in:** #50
- **Success:** `200`
- **Errors:** 404 if missing **or** owned by someone else

Response:

```json
{
  "id": 1,
  "catalogue_id": "V03",
  "make": "Toyota",
  "model": "Corolla",
  "model_year": 2025,
  "powertrain": "petrol",
  "body_style": "sedan",
  "source_market": "US",
  "driving_condition": "normal",
  "regular_dusty_gravel_or_visible_soot": null,
  "last_oil_meets_spec": true,
  "handbook_confirmed": true,
  "nickname": null,
  "reminder_support": "supported",
  "latest_odometer_km": 48000.0,
  "latest_odometer_at": "2026-11-21T09:00:00Z"
}
```

### PATCH `/api/v1/vehicles/{vehicle_id}` — Update vehicle

- **Purpose:** Change configuration fields used by rule matching. Odometer goes through odometer-readings.
- **Auth:** owner
- **Supports:** US-02
- **Implemented in:** #50
- **Success:** `200`
- **Errors:** 404 · 422

Request:

```json
{
  "nickname": "Blue"
}
```

Response:

```json
{
  "id": 1,
  "catalogue_id": "V03",
  "make": "Toyota",
  "model": "Corolla",
  "model_year": 2025,
  "powertrain": "petrol",
  "body_style": "sedan",
  "source_market": "US",
  "driving_condition": "normal",
  "regular_dusty_gravel_or_visible_soot": null,
  "last_oil_meets_spec": true,
  "handbook_confirmed": true,
  "nickname": null,
  "reminder_support": "supported",
  "latest_odometer_km": 48000.0,
  "latest_odometer_at": "2026-11-21T09:00:00Z"
}
```

### DELETE `/api/v1/vehicles/{vehicle_id}` — Delete vehicle

- **Purpose:** Deletes the vehicle with its readings, logs and snoozes.
- **Auth:** owner
- **Supports:** AC-06
- **Implemented in:** #50
- **Success:** `204`
- **Errors:** 404


## Service logs and odometer

### GET `/api/v1/vehicles/{vehicle_id}/service-logs` — Service history

- **Purpose:** Newest first (`service_date` desc, then `id` desc). Paginated.
- **Auth:** owner
- **Supports:** US-04 · Log service
- **Implemented in:** #50
- **Success:** `200`
- **Errors:** 404

Response:

```json
{
  "items": [
    {
      "id": 1,
      "service_key": "engine_oil_and_filter",
      "service_date": "2026-06-01",
      "odometer_km": 40000.0,
      "confirmed": true,
      "oil_meets_spec": true,
      "minder_reset_on": null,
      "notes": "0W-16 synthetic",
      "created_at": "2026-11-21T09:00:00Z"
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 1
}
```

### POST `/api/v1/vehicles/{vehicle_id}/service-logs` — Log service

- **Purpose:** One row per `service_keys` entry (a combined engine+cabin filter job is two keys). Also records the odometer reading if given.
- **Auth:** owner
- **Supports:** US-04 · Log service
- **Implemented in:** #50
- **Success:** `201`
- **Errors:** 400 `future_date` · 409 `odometer_lower_than_latest` unless `confirm_lower: true` · 404 · 422

Request:

```json
{
  "service_keys": [
    "engine_oil_and_filter"
  ],
  "service_date": "2026-06-01"
}
```

Response:

```json
[
  {
    "id": 1,
    "service_key": "engine_oil_and_filter",
    "service_date": "2026-06-01",
    "odometer_km": 40000.0,
    "confirmed": true,
    "oil_meets_spec": true,
    "minder_reset_on": null,
    "notes": "0W-16 synthetic",
    "created_at": "2026-11-21T09:00:00Z"
  }
]
```

### GET `/api/v1/vehicles/{vehicle_id}/odometer-readings` — Odometer history

- **Purpose:** Paginated, newest first.
- **Auth:** owner
- **Supports:** US-02
- **Implemented in:** #50
- **Success:** `200`
- **Errors:** 404

Response:

```json
{
  "items": [
    {
      "id": 1,
      "odometer_km": 48000.0,
      "read_at": "2026-11-21T09:00:00Z",
      "source": "manual"
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 1
}
```

### POST `/api/v1/vehicles/{vehicle_id}/odometer-readings` — Record odometer

- **Purpose:** Add a reading (`source: manual`). `read_at` defaults to now.
- **Auth:** owner
- **Supports:** US-02, US-05
- **Implemented in:** #50
- **Success:** `201`
- **Errors:** 400 `future_reading` · 409 `odometer_lower_than_latest` unless `confirm_lower` · 422 negative

Request:

```json
{
  "odometer_km": 53000
}
```

Response:

```json
{
  "id": 1,
  "odometer_km": 48000.0,
  "read_at": "2026-11-21T09:00:00Z",
  "source": "manual"
}
```


## Reminders

### GET `/api/v1/vehicles/{vehicle_id}/reminders` — Reminder view

- **Purpose:** Computed on read by the rule engine. `schedule: unknown` → show "Schedule unknown" with `help_link`. Each card has state in words (`state_label`), thresholds, last service, sources, missing fields.
- **Auth:** owner
- **Supports:** US-05, US-06, US-07 · Reminder view
- **Implemented in:** #44 (engine), #50
- **Success:** `200`
- **Errors:** 404

Response:

```json
{
  "vehicle_id": 1,
  "evaluated_on": "2026-11-21",
  "schedule": "supported",
  "reminders": [
    {
      "rule_id": "R01",
      "service_key": "engine_oil_and_filter",
      "label": "Replace engine oil and filter",
      "state": "approaching",
      "state_label": "Approaching",
      "trigger": "distance",
      "due_date": "2027-06-01",
      "due_odometer_km": 56093.44,
      "interval_months": 12,
      "interval_km": 16093.44,
      "last_service": {
        "service_date": "2026-06-01",
        "odometer_km": 40000.0
      },
      "current_odometer_km": 53000.0,
      "odometer_stale": false,
      "missing_fields": [],
      "explanation": "13,000 km of 16,093 km since your last oil change (81%). Due by 1 June 2027.",
      "sources": [
        {
          "source_id": "S1",
          "title": "Toyota 2025 Corolla maintenance guide",
          "url": "https://www.toyota.com/content/dam/toyota/brochures/pdf/2025/T-MMS-25Corolla.pdf"
        }
      ],
      "snoozed_until": null,
      "search_service": "oil_service",
      "help_link": null
    }
  ]
}
```

### POST `/api/v1/vehicles/{vehicle_id}/reminders/{rule_id}/snooze` — Snooze

- **Purpose:** Hide a card until a date. Stored in `reminder_snoozes`.
- **Auth:** owner
- **Supports:** Reminder view
- **Implemented in:** #44
- **Success:** `200`
- **Errors:** 404 rule not applicable to this vehicle · 422

Request:

```json
{
  "service_key": "engine_oil_and_filter",
  "until": "2026-12-01"
}
```

Response:

```json
{
  "rule_id": "R01",
  "service_key": "engine_oil_and_filter",
  "label": "Replace engine oil and filter",
  "state": "approaching",
  "state_label": "Approaching",
  "trigger": "distance",
  "due_date": "2027-06-01",
  "due_odometer_km": 56093.44,
  "interval_months": 12,
  "interval_km": 16093.44,
  "last_service": {
    "service_date": "2026-06-01",
    "odometer_km": 40000.0
  },
  "current_odometer_km": 53000.0,
  "odometer_stale": false,
  "missing_fields": [],
  "explanation": "13,000 km of 16,093 km since your last oil change (81%). Due by 1 June 2027.",
  "sources": [
    {
      "source_id": "S1",
      "title": "Toyota 2025 Corolla maintenance guide",
      "url": "https://www.toyota.com/content/dam/toyota/brochures/pdf/2025/T-MMS-25Corolla.pdf"
    }
  ],
  "snoozed_until": "2026-12-01",
  "search_service": "oil_service",
  "help_link": null
}
```

### POST `/api/v1/vehicles/{vehicle_id}/reminders/{rule_id}/complete` — Mark done

- **Purpose:** Shortcut for logging that service; returns the re-evaluated card.
- **Auth:** owner
- **Supports:** US-04, US-05
- **Implemented in:** #44, #50
- **Success:** `201`
- **Errors:** Same as POST service-logs

Request:

```json
{
  "service_key": "engine_oil_and_filter",
  "service_date": "2026-11-20"
}
```

Response:

```json
{
  "rule_id": "R01",
  "service_key": "engine_oil_and_filter",
  "label": "Replace engine oil and filter",
  "state": "ok",
  "state_label": "Up to date",
  "trigger": "distance",
  "due_date": "2027-06-01",
  "due_odometer_km": 56093.44,
  "interval_months": 12,
  "interval_km": 16093.44,
  "last_service": {
    "service_date": "2026-06-01",
    "odometer_km": 40000.0
  },
  "current_odometer_km": 53000.0,
  "odometer_stale": false,
  "missing_fields": [],
  "explanation": "13,000 km of 16,093 km since your last oil change (81%). Due by 1 June 2027.",
  "sources": [
    {
      "source_id": "S1",
      "title": "Toyota 2025 Corolla maintenance guide",
      "url": "https://www.toyota.com/content/dam/toyota/brochures/pdf/2025/T-MMS-25Corolla.pdf"
    }
  ],
  "snoozed_until": null,
  "search_service": "oil_service",
  "help_link": null
}
```

### GET `/api/v1/vehicles/{vehicle_id}/minder-prompts` — List Minder prompts

- **Purpose:** Driver-reported Honda Maintenance Minder codes, active and cleared, newest first.
- **Auth:** owner
- **Supports:** RT-15 · Reminder view
- **Implemented in:** #44
- **Success:** `200`
- **Errors:** 404

Response:

```json
[
  {
    "id": 1,
    "code": "7",
    "reported_at": "2026-11-24T08:00:00Z",
    "cleared_at": null
  }
]
```

### POST `/api/v1/vehicles/{vehicle_id}/minder-prompts` — Report Minder prompt

- **Purpose:** The dashboard is authoritative: the matching reminder card becomes due now with `trigger: dashboard`. Server sets `reported_at`.
- **Auth:** owner
- **Supports:** RT-15 · Reminder view
- **Implemented in:** #44
- **Success:** `201`
- **Errors:** 400 `not_a_minder_vehicle` · 404 · 422

Request:

```json
{
  "code": "7"
}
```

Response:

```json
{
  "id": 1,
  "code": "7",
  "reported_at": "2026-11-24T08:00:00Z",
  "cleared_at": null
}
```

### POST `/api/v1/vehicles/{vehicle_id}/minder-prompts/{prompt_id}/clear` — Clear Minder prompt

- **Purpose:** The prompt is gone from the dashboard (for example after the service and a Minder reset).
- **Auth:** owner
- **Supports:** RT-15
- **Implemented in:** #44
- **Success:** `200`
- **Errors:** 404

Response:

```json
{
  "id": 1,
  "code": "7",
  "reported_at": "2026-11-24T08:00:00Z",
  "cleared_at": "2026-11-25T08:00:00Z"
}
```


## Mechanics

### GET `/api/v1/service-categories` — Service list

- **Purpose:** Search picker. `searchable: false` items (EV high-voltage) are shown as unavailable, not searchable.
- **Auth:** none
- **Supports:** US-08 · Mechanic search
- **Implemented in:** #45
- **Success:** `200`
- **Errors:** —

Response:

```json
[
  {
    "id": "brake_service",
    "label": "Brake service",
    "searchable": true
  }
]
```

### GET `/api/v1/neighbourhoods` — Neighbourhood list

- **Purpose:** Typed-area picker. Names only; centroids stay server-side.
- **Auth:** none
- **Supports:** US-08, US-09
- **Implemented in:** #45
- **Success:** `200`
- **Errors:** —

Response:

```json
[
  {
    "name": "Osu"
  }
]
```

### GET `/api/v1/mechanics/search` — Search

- **Purpose:** Query: `service` (required), exactly one origin — `neighbourhood` **or** `lat`+`lng` — `radius_km` 10/20/40 (default 10), `include_unavailable` (default false). Filtering and ranking follow the matching spec (distance to 0.1 km, newest report, stable ID). `suggest_radius_km` set when `assessed` is empty below 40 km. `hidden_unavailable` counts unavailable matches left out, for the "include unavailable" control. Coordinates are never stored or logged.
- **Auth:** none
- **Supports:** US-08, US-09, US-10 · Mechanic search
- **Implemented in:** #45
- **Success:** `200`
- **Errors:** 422 malformed/both/no origin or bad radius · 400 `unsupported_service` (incl. `ev_high_voltage`) · 400 `unknown_neighbourhood` with `details.suggestions`

Response:

```json
{
  "service": "brake_service",
  "radius_km": 10,
  "origin_precision": "neighbourhood",
  "assessed": [
    {
      "id": "M01",
      "name": "DEMO - Kojo Auto Works",
      "neighbourhood": "Osu",
      "distance_km": 0.0,
      "availability": {
        "status": "available",
        "reported_status": "available",
        "reported_at": "2026-11-23T06:00:00Z"
      },
      "assessment_status": "assessed",
      "service_verification": "assessed",
      "assessed_on": "2026-11-15",
      "is_demo": true
    }
  ],
  "not_assessed": [],
  "suggest_radius_km": null,
  "hidden_unavailable": 1,
  "message": null
}
```

### GET `/api/v1/mechanics/{mechanic_id}` — Mechanic profile

- **Purpose:** Assessed vs other services listed separately; availability with `reported_at` for "updated X hours ago"; contact is a demo dialog for demo records.
- **Auth:** none
- **Supports:** US-11 · Mechanic profile
- **Implemented in:** #45
- **Success:** `200`
- **Errors:** 404 suspended, unpublished, or demo record outside demo mode

Response:

```json
{
  "id": "M01",
  "name": "DEMO - Kojo Auto Works",
  "neighbourhood": "Osu",
  "service_radius_km": 10.0,
  "assessment_status": "assessed",
  "assessed_on": "2026-11-15",
  "assessor": "Nkenten demo assessor (fictional)",
  "assessment_basis": "Fictional sprint fixture. Service-specific practical assessment.",
  "assessed_services": [
    {
      "category": "brake_service",
      "label": "Brake service",
      "verification": "assessed",
      "assessed_on": "2026-11-15"
    }
  ],
  "other_services": [
    {
      "category": "diagnostics",
      "label": "Diagnostics",
      "verification": "self_reported",
      "assessed_on": null
    }
  ],
  "availability": {
    "status": "available",
    "reported_status": "available",
    "reported_at": "2026-11-23T06:00:00Z"
  },
  "contact": {
    "mode": "demo_dialog",
    "display_name": "DEMO - Kojo Auto Works",
    "phone": null
  },
  "is_demo": true
}
```

### PUT `/api/v1/mechanics/{mechanic_id}/availability` — Report availability

- **Purpose:** Server sets `reported_at`; change is logged.
- **Auth:** mechanic (own) or admin
- **Supports:** US-13
- **Implemented in:** #45
- **Success:** `200`
- **Errors:** 403 not own listing · 404

Request:

```json
{
  "status": "busy"
}
```

Response:

```json
{
  "status": "busy",
  "reported_status": "busy",
  "reported_at": "2026-11-23T06:00:00Z"
}
```


## Admin

### GET `/api/v1/admin/mechanics` — List listings

- **Purpose:** All listings incl. suspended, unpublished, demo. `?status=` filter. Paginated.
- **Auth:** admin
- **Supports:** Admin: review
- **Implemented in:** #49
- **Success:** `200`
- **Errors:** 401 · 403

Response:

```json
{
  "items": [
    {
      "id": "M01",
      "name": "DEMO - Kojo Auto Works",
      "neighbourhood": "Osu",
      "service_radius_km": 10.0,
      "assessment_status": "assessed",
      "assessed_on": "2026-11-15",
      "assessor": "Nkenten demo assessor (fictional)",
      "assessment_basis": "Fictional sprint fixture. Service-specific practical assessment.",
      "assessed_services": [
        {
          "category": "brake_service",
          "label": "Brake service",
          "verification": "assessed",
          "assessed_on": "2026-11-15"
        }
      ],
      "other_services": [
        {
          "category": "diagnostics",
          "label": "Diagnostics",
          "verification": "self_reported",
          "assessed_on": null
        }
      ],
      "availability": {
        "status": "available",
        "reported_status": "available",
        "reported_at": "2026-11-23T06:00:00Z"
      },
      "contact": {
        "mode": "demo_dialog",
        "display_name": "DEMO - Kojo Auto Works",
        "phone": null
      },
      "is_demo": true,
      "published": true,
      "suspension_reason": null,
      "history": []
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 1
}
```

### GET `/api/v1/admin/mechanics/{mechanic_id}` — Listing detail

- **Purpose:** Includes `history` (audit log).
- **Auth:** admin
- **Supports:** MT-14
- **Implemented in:** #49
- **Success:** `200`
- **Errors:** 403 · 404

Response:

```json
{
  "id": "M01",
  "name": "DEMO - Kojo Auto Works",
  "neighbourhood": "Osu",
  "service_radius_km": 10.0,
  "assessment_status": "assessed",
  "assessed_on": "2026-11-15",
  "assessor": "Nkenten demo assessor (fictional)",
  "assessment_basis": "Fictional sprint fixture. Service-specific practical assessment.",
  "assessed_services": [
    {
      "category": "brake_service",
      "label": "Brake service",
      "verification": "assessed",
      "assessed_on": "2026-11-15"
    }
  ],
  "other_services": [
    {
      "category": "diagnostics",
      "label": "Diagnostics",
      "verification": "self_reported",
      "assessed_on": null
    }
  ],
  "availability": {
    "status": "available",
    "reported_status": "available",
    "reported_at": "2026-11-23T06:00:00Z"
  },
  "contact": {
    "mode": "demo_dialog",
    "display_name": "DEMO - Kojo Auto Works",
    "phone": null
  },
  "is_demo": true,
  "published": true,
  "suspension_reason": null,
  "history": []
}
```

### PUT `/api/v1/admin/mechanics/{mechanic_id}/assessment` — Update assessment

- **Purpose:** Overall status and per-service verification. Marking a service `assessed` requires `assessor` and `assessed_on`; `suspended` requires `suspension_reason` and removes the listing from search at once. Every change is logged.
- **Auth:** admin
- **Supports:** US-12, US-14 · Admin: review
- **Implemented in:** #49
- **Success:** `200`
- **Errors:** 422 missing assessor/date/reason · 403 · 404

Request:

```json
{
  "assessment_status": "suspended",
  "suspension_reason": "Complaint upheld"
}
```

Response:

```json
{
  "id": "M01",
  "name": "DEMO - Kojo Auto Works",
  "neighbourhood": "Osu",
  "service_radius_km": 10.0,
  "assessment_status": "assessed",
  "assessed_on": "2026-11-15",
  "assessor": "Nkenten demo assessor (fictional)",
  "assessment_basis": "Fictional sprint fixture. Service-specific practical assessment.",
  "assessed_services": [
    {
      "category": "brake_service",
      "label": "Brake service",
      "verification": "assessed",
      "assessed_on": "2026-11-15"
    }
  ],
  "other_services": [
    {
      "category": "diagnostics",
      "label": "Diagnostics",
      "verification": "self_reported",
      "assessed_on": null
    }
  ],
  "availability": {
    "status": "available",
    "reported_status": "available",
    "reported_at": "2026-11-23T06:00:00Z"
  },
  "contact": {
    "mode": "demo_dialog",
    "display_name": "DEMO - Kojo Auto Works",
    "phone": null
  },
  "is_demo": true,
  "published": true,
  "suspension_reason": null,
  "history": []
}
```

### GET `/api/v1/admin/mechanics/{mechanic_id}/complaints` — List complaints

- **Purpose:** Complaints for one listing.
- **Auth:** admin
- **Supports:** US-14 · Admin: complaints
- **Implemented in:** #49
- **Success:** `200`
- **Errors:** 403 · 404

Response:

```json
[
  {
    "id": 1,
    "mechanic_id": "M08",
    "description": "Demo complaint",
    "mechanic_response": null,
    "status": "open",
    "created_at": "2026-11-23T06:00:00Z",
    "resolved_at": null
  }
]
```

### POST `/api/v1/admin/mechanics/{mechanic_id}/complaints` — Record complaint

- **Purpose:** New complaint, status `open`.
- **Auth:** admin
- **Supports:** US-14
- **Implemented in:** #49
- **Success:** `201`
- **Errors:** 403 · 404 · 422

Request:

```json
{
  "description": "No-show"
}
```

Response:

```json
{
  "id": 1,
  "mechanic_id": "M08",
  "description": "Demo complaint",
  "mechanic_response": null,
  "status": "open",
  "created_at": "2026-11-23T06:00:00Z",
  "resolved_at": null
}
```

### PATCH `/api/v1/admin/complaints/{complaint_id}` — Respond / resolve

- **Purpose:** Attach mechanic response and/or set `dismissed` / `upheld`. Upholding does **not** auto-suspend; use the assessment endpoint.
- **Auth:** admin
- **Supports:** US-14
- **Implemented in:** #49
- **Success:** `200`
- **Errors:** 403 · 404

Request:

```json
{
  "status": "upheld"
}
```

Response:

```json
{
  "id": 1,
  "mechanic_id": "M08",
  "description": "Demo complaint",
  "mechanic_response": null,
  "status": "open",
  "created_at": "2026-11-23T06:00:00Z",
  "resolved_at": null
}
```

