# Availability and reliability calculations
**Nkenten AutoCare · Sprint 1 · Germain and Isaac · 21 November 2026**

## Measurement

Measure the FastAPI health endpoint, the authenticated reminder workflow using a fixed supported vehicle and service event, and the mechanic search workflow using a fixed fixture. Run probes every minute for 72 hours during the proposed 11–14 December test period, from a separate process or host. A probe succeeds when the expected status and body arrive within 2 seconds. Check the known rule and state for reminders (freeze or account for clock changes) and the expected IDs and labels for mechanic search. Record onset, status, correctness, elapsed ms, probe outcome, deployment/fixture version, timestamps in UTC, and the environment. Include planned application downtime in this user-facing measure.

Count each scheduled slot as up, down or unknown. Network or HTTP failure observed by a functioning probe is down when consistent with its perspective. Missing telemetry or a failed monitor is unknown. Count durations with a single rule, one minute per observed slot, and report the sampling resolution. Clip to the reporting window. Report probe coverage and availability bounds whenever unknown minutes can change the result. Count one incident on a consecutive observed up→down transition. A gap breaks the chain, and outages already in progress at window start are left-censored. For repair time, use only outages with an observed onset and recovery and no unknown gap. Report outages that cross either boundary separately.

## Formulas

Let U, D and X be observed up, observed down and unknown time. Use hours for intensity and mission time.

| Metric | Formula | Interpretation |
|---|---|---|
| Observed time availability | A = U / (U + D) | With full coverage this is uptime divided by total observation time |
| Coverage and bounds | C = (U + D) / (U + D + X); bounds U/T to (U + X)/T, with T = U + D + X | If U + D = 0, observed availability is undefined |
| Operating-time failure rate | λ̂ = n / U | n is confirmed up→down onsets. If U = 0, undefined. Gaps can hide failures and bias the estimate |
| Estimated MTBF | U / n | Mean operating hours per observed failure under the constant-rate model. If n = 0, report no finite estimate |
| Estimated MTTR | Σ duration of complete observed outages / number of complete observed outages | Undefined if no completed outage is observed |
| Steady-state availability model | A ≈ MTBF / (MTBF + MTTR) | Assumes representative alternating operation and repair. Do not force equality with observed A under censoring |
| Mission reliability | R(t) = exp(−λ̂t) | Conditional on starting up and assuming a constant rate for the stated configuration and workload |
| Probability of one or more failures | F(t) = 1 − R(t) | Complement of mission reliability |

When n = 0 with positive observed uptime, report “zero observed failures in U hours” and keep the reliability conclusion unestimated. Under the stated Poisson model and adequate coverage, an optional one-sided 95% upper bound for λ is −ln(0.05)/U. Changes in deployment, load and operating conditions can violate the constant-rate model. Prefer direct end-to-end probes for shared infrastructure. An independent series model uses the product of component reliabilities only when independence and the same mission time are defensible. Workflow probe aggregates already include shared dependencies.

## Worked example using simulated data

A 72 h window has 4,320 scheduled one-minute probes, full coverage, and three complete outages of 4, 6 and 2 minutes. This gives D = 0.20 h and U = 71.80 h.

| Metric | Calculation | Result |
|---|---|---:|
| Availability | 71.8 / 72 | 99.7222% |
| MTBF | 71.8 / 3 | 23.9333 h |
| MTTR | 12 min / 3 | 4 min |
| Failure rate | 3 / 71.8 | 0.04178 per hour |
| 30-minute reliability | exp(−(3 / 71.8) × 0.5) | 97.93% |
| Probability of ≥1 failure in 30 minutes | 1 − exp(−(3 / 71.8) × 0.5) | 2.07% |
| 8-hour reliability | exp(−(3 / 71.8) × 8) | 71.59% |

For each endpoint report the observation period, environment, probe interval, count of up/down/missing slots, incident counts including censored observations, availability and coverage, mission time, assumptions, and whether values are measured, simulated, or collected during controlled fault injection.

- [Google Cloud CRE availability definitions](https://cloud.google.com/blog/products/gcp/available-or-not-that-is-the-question-cre-life-lessons/)
- [NIST exponential reliability model](https://www.itl.nist.gov/div898/handbook/apr/section1/apr161.htm)
