# Reminder rule specification
**Nkenten AutoCare · Sprint 1 · Germain and Isaac · 21 November 2026**

The reminder compares a supported vehicle’s time and distance since a confirmed service or reset with the relevant manufacturer threshold. The JSON is the implementation contract for rules, sources and applicability. Use the earlier applicable deadline.

## Supported configurations

| Model | Source market | Eligible configuration |
|---|---|---|
| Corolla | United States | 2023–2025 petrol sedan |
| Camry | United States | 2023–2024 petrol sedan and 2025 hybrid sedan |
| CR-V | Canada | 2025 petrol or hybrid SUV |

Use the vehicle’s original sales market and model year. Ask the driver to confirm the handbook and configuration. A vehicle driven in Ghana can be a matching import. Toyota/CFAO Ghana describes its service programme but the Ghana page reviewed does not publish these model-specific thresholds. Other markets, unknown markets and unverified variants get **Unknown** and a link to the manual or mechanic search. Even within a catalogue band, only the exact applicability objects in the seed enable rules.

## Rules

| ID | Vehicle | Action | Condition | Source mi | App km | Months | Source |
|---|---|---|---|---:|---:|---:|---|
| R01 | Toyota Corolla | Replace engine oil and filter | `normal_recommended_oil` | 10,000 | 16,093 | 12 | S2, S6, S1 |
| R02 | Toyota Corolla | Replace engine oil and filter | `primarily_dirt_or_dusty` | 5,000 | 8,047 | 6 | S2, S6, S1 |
| R03 | Toyota Corolla | Rotate tyres | `base_schedule` | 5,000 | 8,047 | 6 | S2, S6, S1 |
| R04 | Toyota Corolla | Inspect brakes visually | `base_schedule` | 5,000 | 8,047 | 6 | S2, S6, S1 |
| R05 | Toyota Corolla | Replace cabin air filter | `normal` | 30,000 | 48,280 | 36 | S2, S6, S1 |
| R07 | Toyota Camry | Replace engine oil and filter | `normal_recommended_oil` | 10,000 | 16,093 | 12 | S4, S7, S3 |
| R08 | Toyota Camry | Replace cabin air filter | `normal` | 10,000 | 16,093 | 12 | S4, S7, S3 |
| R09 | Honda CR-V | Replace engine oil | `minder_fallback` | — | — | 12 | S5, S8 |
| R10 | Honda CR-V | Replace engine and cabin air filters | `regular_dusty_gravel_or_visible_soot` | — | 24,000 | — | S5, S8 |
| R11 | Honda CR-V | Replace brake fluid | `minder_fallback` | — | — | 36 | S5, S8 |

Toyota mile values are canonical. Convert using 1 mi = 1.609344 km. The table and seed show nearest whole kilometres for display. Preserve decimal precision internally and compare against the exact converted threshold. At 10,000 mi, the exact threshold is 16,093.44 km, displayed as about 16,093 km. For a whole-km odometer, the first qualifying integer is 16,094. Honda prints 24,000 km directly. A dash means the manufacturer supplies that threshold through the vehicle or leaves the dimension unspecified. Keep the corresponding interval null.

- Corolla base tyre and brakes rules run for any identified operating condition. R02 takes precedence over R01 for primarily dirt or dusty roads. If another special-use condition applies, or the previous oil grade is unknown or does not meet the source, do not use the normal oil interval. Use the matched special rule only if its own conditions are met. Applies equally to the Camry normal oil guard. A dust-exposed or other special-use Camry requires its own manual check for oil.
- The Toyota standard cabin-filter rows apply to normal operation. If heavy traffic, dust or other source-listed exposure may shorten filter life, return Unknown for the shortened schedule and explain the manual guidance.
- Honda rules use the **Canadian** A/0 schedule. R10 applies when regularly on dusty gravel roads or in areas with visible airborne soot. Track engine and cabin filters independently so changing one cannot reset the other. The cards share R10 with separate service-history keys `engine_air_filter` and `cabin_air_filter`. A combined event may create both records only when both replacements are confirmed. For R09, an oil-and-filter record can serve as the oil record only if an identified Maintenance Minder reset is linked. R11 ties to brake fluid history and item 7.
- The CR-V dashboard is authoritative for earlier prompts. Display any driver-reported active prompt for the corresponding service separately and mark it due immediately. A reminder card based on a fixed fallback shows “Check the Maintenance Minder for earlier service” and does not report absent dashboard data as clear. Calculate R09 from a confirmed oil service and reset, using the earlier date if they differ and the data has been verified. R11 uses confirmed brake fluid history. A missing anchor returns Unknown.
- R06 from the draft is retired. The Corolla first-fill coolant milestone and follow-up coolant interval require separate anchors and tests before activation.

## Evaluation contract

1. Validate inputs. Reject negative or non-finite distances, invalid units, future service or reset dates, and odometer rollback through the normal write path. If legacy data is inconsistent or a vehicle has an unverified odometer replacement, show Unknown with a correction prompt. Evaluate dates in Africa/Accra. Track the timestamp of the current reading. Mark readings older than 30 days as stale for distance calculations and request an update. This freshness window is a prototype decision. If it predates the service or is absent, the distance dimension is unknown.
2. Select across make, model, model year, source market, powertrain, body style and service. Apply conditions above. Overlapping rules for the same service and condition are an invalid seed. Do not infer a service from purchase or registration.
3. Use the latest confirmed matching service (service date then stable event ID). Calculate `distance_ratio = distance_since_service_km / exact_interval_km`. Compute `due_date = add_calendar_months(anchor_date, interval_months)`, clamping to the last day of the target month. Compute `time_ratio = elapsed_calendar_days / days_between(anchor_date, due_date)`. Apply inclusive 80% and 100% comparisons before rounding either display value.
4. If either known dimension reaches 100%, report **Overdue**. If either reaches 80% and the other applicable dimension is missing, report **Approaching** with “other threshold unknown.” If every applicable dimension is known and below 80%, report **OK**. If all known dimensions are below 80% and an applicable dimension is unknown, report **Unknown**. Disabled dimensions never count as missing. Use “Due today” at the exact date and “Due now” at the distance threshold.
5. Return `rule_id`, `state`, `trigger` (time, distance, both, dashboard or n/a), present `due_date` and `due_odometer_km`, available readings, missing fields, and the matched source for that configuration. Use text labels and accessible icons. If one threshold is unknown, explain which one and solicit the missing data.

**Worked example.** A US 2025 Corolla petrol sedan in normal use had its oil and filter replaced on 1 June 2026 at 40,000 km with the specified oil. R01 gives a due date of 1 June 2027 and an exact target of 56,093.44 km. On 21 November 2026 at 48,000 km the state is OK. At 53,000 km it is Approaching by distance. If driven primarily on dusty roads, R02 applies and 48,047 km is the first whole-km reading at which the distance trigger fires. A Canadian 2025 CR-V with a confirmed brake-fluid replacement on 30 November 2023 and no active item 7 reaches the fallback date on 30 November 2026.

## Manufacturer sources

- S1 · [Toyota 2025 Corolla (US petrol sedan), maintenance charts and footnotes, pp. 36–43](https://www.toyota.com/content/dam/toyota/brochures/pdf/2025/T-MMS-25Corolla.pdf)
- S2 · [Toyota 2023 Corolla (US petrol sedan), maintenance log, pp. 36–53](https://www.toyota.com/content/dam/toyota/brochures/pdf/2023/T-MMS-23Corolla.pdf)
- S3 · [Toyota 2025 Camry (US hybrid), maintenance log and footnotes, pp. 40–45](https://www.toyota.com/content/dam/toyota/brochures/pdf/2025/T-MMS-25Camry.pdf)
- S4 · [Toyota 2023 Camry (US petrol), maintenance log, pp. 36–53](https://www.toyota.com/content/dam/toyota/brochures/pdf/2023/T-MMS-23Camry.pdf)
- S5 · [Honda Canada Maintenance Minder A/0, codes A/0, 2 and 7 and exceptional-use notes](https://www.honda.ca/-/media/Brands/Honda/Maintenance-Schedule/PDF/Maintenance-Minder-A0-Schedule---ENG.pdf?rev=7ee34cf6ecf34e3c8fe343b7a090eab2)
- S6 · [Toyota 2024 Corolla (US petrol sedan), maintenance log, pp. 36–53](https://www.toyota.com/content/dam/toyota/brochures/pdf/2024/T-MMS-24Corolla.pdf)
- S7 · [Toyota 2024 Camry (US petrol), maintenance log, pp. 36–53](https://www.toyota.com/content/dam/toyota/brochures/pdf/2024/T-MMS-24Camry.pdf)
- S8 · [Honda Canada Maintenance Minder vehicle applicability](https://www.honda.ca/en/service-parts/maintenance-schedules)
- S9 · [Toyota/CFAO Ghana periodic maintenance service information](https://toyotacfao.com/gh/en/periodic-maintenance)
