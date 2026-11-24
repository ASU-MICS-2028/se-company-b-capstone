# Mechanic matching specification
**Nkenten AutoCare · Sprint 1 · Germain and Isaac · 21 November 2026**

## Request and result

`GET /api/v1/mechanics/search` accepts a searchable service ID, either a neighbourhood name or a complete latitude/longitude pair, radius 10/20/40 km (default 10), and `include_unavailable` (default false). Resolve neighbourhoods using trim, Unicode normalization and case-insensitive matching against the seed. Use the approximate centroid only after selection. Location permission denial leads to the neighbourhood picker. Accept finite latitude in [-90,90] and longitude in [-180,180]. A malformed coordinate pair, both origins, missing origin or invalid radius returns 422. A well-formed request with an unknown neighbourhood or unsupported service returns 400 with a reason code. Provide supported neighbourhood suggestions when possible. The high-voltage category has `searchable: false`.

Return `assessed`, `not_assessed`, `suggest_radius_km`, `origin_precision` and `message`. Entries include mechanic ID, display name, neighbourhood, distance in km, effective availability, reported timestamp, assessment and per-service verification, assessment date and `is_demo`. Fetch profile at `GET /api/v1/mechanics/{id}` with assessment basis and applicable contact option. A suspended profile returns 404 to drivers. Demo records and demo contact actions are available in demo mode only. The demo contact action opens a local dialog showing the fictional garage name. Live contact details are returned on the profile only.

## Filter and ranking

1. Use one snapshot of the listings and capture the UTC evaluation time once. Exclude suspended or unpublished listings, demo listings outside demo mode, and listings missing the requested service or valid location/service-area information.
2. Compute great-circle distance using Haversine, Earth radius 6,371 km. Clamp the intermediate value to [0,1] for numerical stability. Keep the unrounded distance for both filters. Include a candidate only if distance is within both the driver's radius and the candidate’s service radius. Boundary equality passes. Show a straight-line distance label.
3. Resolve availability before filtering. A valid status published up to and including 24 h ago is current for this query. Missing, invalid, future-dated or older reports give `unknown`. Retain the last valid historical timestamp for a stale report. Exclude a currently reported unavailable mechanic unless `include_unavailable` is true. A stale unavailable report becomes unknown and can be displayed. Busy and unknown both pass. Show “Last reported” or “Availability unknown” with the update time if available.
4. Place a result in `assessed` only if the overall assessment and the requested service are both assessed. Place pending and self-reported results in `not_assessed`, including an assessed mechanic with a self-reported skill for the requested service. Present that list as a collapsed section with a service-specific label.
5. Sort each list by the distance rounded to 0.1 km, then by the newest valid nonfuture report timestamp (missing last), then by ascending stable ID. Use half-up decimal rounding for display and ties. Availability labels add no priority. Each result's distance is approximate and a report does not imply a response or arrival time.
6. If assessed is empty at 10 or 20 km, offer the next radius. At 40 km, show a service-specific empty message plus any separate self-reported results. Handle no available candidate through the explicit include-unavailable control. Keep consent-based location in memory for the request and redact exact coordinates from logging and analytics. Disable access to suspended profiles even if their IDs were known earlier.

## Reminder to search mapping

A reminder card's "Find a mechanic" action searches the category below for the rule's `service_type`. A row marked **disabled** has no search link.

| Rule `service_type` | Rules | Search `service` |
|---|---|---|
| `engine_oil_and_filter` | R01, R02, R07 | `oil_service` |
| `engine_oil` | R09 | `oil_service` |
| `tyre_rotation` | R03 | `tyre_service` |
| `brake_inspection` | R04 | `brake_service` |
| `brake_fluid` | R11 | `brake_service` |
| `cabin_air_filter` | R05, R08 | **disabled** |
| `engine_and_cabin_air_filter` | R10 | **disabled** |

The two air-filter search links are disabled. No service category records that a mechanic handles the specific filter replacement, and pointing drivers to a broader category such as `air_conditioning` or `oil_service` would imply an assessment the platform does not hold. For these rules the reminder card still shows its state, threshold and source, but it shows no "Find a mechanic" action and the API returns no search `service` for them. Enable a link only after a category or per-service assessment confirms that the mechanic handles that filter replacement, and update this table in the same change.

## Fixture examples and expected order

Evaluate at the seed reference time `2026-11-23T08:00:00Z`. If demo availability timestamps are shifted for a live demo, use a single constant offset across the fixture. Tests use the fixed timestamp.

| Case | Service and area | Radius / flag | Assessed | Other | Outcome |
|---|---|---|---|---|---|
| MT-01 | brake_service, Osu | 10 | M01, M02 | — | M01 available, M02 busy. M07 is currently unavailable, M08 suspended |
| MT-02 | brake_service, Osu | 10, include unavailable | M01, M02, M07 | — | M07 labelled unavailable |
| MT-03 | brake_service, Osu | 20 | M01, M02 | M06 | M04 excluded by its own service radius |
| MT-04 | oil_service, East Legon | 10 | M03, M04, M01 | M06 | M03 stale and displayed unknown |
| MT-05 | air_conditioning, Adenta | 40 | — | M05 | No assessed match, terminal radius |
| MT-06 | suspension_steering, Osu | 10 | — | — | Offer 20 km |
| MT-07 | tyre_service, Osu | 40 | M01, M02, M10 | — | M10 passes its own 30 km service radius |
| MT-08 | ev_high_voltage | any valid origin | — | — | HTTP 400 unsupported service |
| MT-09 | diagnostics, Osu | 10 | M03 | M01 | M01's diagnostics claim is self-reported |
| MT-10 | brake_service, Nkawkaw | 10 | — | — | HTTP 400 unsupported neighbourhood |

For new live profiles record evidence for overall status and each assessed category. Publish only approved profiles. The fixture coordinates reflect approximate neighbourhood centres and are intended for demo and tests. For deployment use an approved geospatial source and verify mechanic locations.
