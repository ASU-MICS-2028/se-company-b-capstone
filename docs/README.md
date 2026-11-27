# Nkenten AutoCare · Sprint 1 Intelligence and Quality
**Germain and Isaac · 21 November 2026**

| Deliverable | Files |
|---|---|
| Ten sourced maintenance reminder rules for selected Corolla, Camry and CR-V configurations | [Rule specification](rules/01-reminder-rule-spec.md) · [Rules JSON](../data/seed/maintenance_rules.json) |
| Mechanic filters, ranking, fallbacks and edge cases | [Matching specification](rules/02-mechanic-matching-spec.md) |
| Catalogue and ten labelled fictional mechanic records | [Vehicle catalogue](../data/seed/vehicles.json) · [Mechanics JSON](../data/seed/mechanics.json) |
| Tests from rule boundaries to end-to-end workflows | [Test plan](test/03-test-plan-outline.md) |
| Thirteen scored risks with triggers, owners and responses | [Risk register](risk/04-risk-register-v1.md) · [Editable CSV](risk/risk-register-v1.csv) |
| Availability and reliability formulas, probe method and simulated example | [Quality calculations](test/05-availability-reliability.md) |
| Steps, source decisions and package verification | [Work log](test/06-steps-and-verification.md) |

The vehicle catalogue retains the eight starter rows from the sprint draft. A catalogue hit can be used for data entry. An active reminder also requires an exact rule applicability match and confirmed history. Other vehicles can be entered manually. The README and verification log record how the expanded research can inform later coverage.

The JSON files use UTF-8. Import rules after the vehicle catalogue. Import mechanics only in the intended demo and test environment. Resolve the stable rule, catalogue, service and mechanic IDs within the seed files before serving the fixture. For automated matching tests, use `seed_reference_time` as written. The test plan defines checks for the eventual application. Availability and reliability figures in the worked example are simulated.
