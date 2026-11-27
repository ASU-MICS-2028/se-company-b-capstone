# Risk register v1
**Nkenten AutoCare · Sprint 1 · Germain and Isaac · 21 November 2026**

Score = likelihood × impact. Rate likelihood from 1 Rare to 5 Almost certain. Rate impact from 1 Minor to 5 Severe. High = 15–25, Medium = 8–14, Low = 1–7. All items start open. Review at each sprint check-in and again before the 10 December demonstration. Record status, evidence and residual score after controls are tested. Owners outside the Intelligence and Quality assignment are proposed.

| ID | Risk | Category | L | I | Score | Priority | Owner | Status |
|---|---|---|---:|---:|---:|---|---|---|
| R-01 | Incorrect maintenance interval or trigger | Safety | 3 | 5 | 15 | High | Germain | Open |
| R-02 | Unqualified provider presented as assessed | Trust | 2 | 5 | 10 | Medium | Isaac | Open |
| R-03 | Driver data or precise search location exposed | Privacy | 2 | 5 | 10 | Medium | Eugene (proposed) | Open |
| R-04 | Low mechanic participation | Adoption | 4 | 3 | 12 | Medium | Alice and Elise (proposed) | Open |
| R-05 | Small or unrepresentative usability sample | Research | 4 | 2 | 8 | Medium | Alice and Elise (proposed) | Open |
| R-06 | Stale availability presented as current | Product | 4 | 3 | 12 | Medium | Isaac | Open |
| R-07 | Inaccurate distance or service-area filtering | Product | 3 | 2 | 6 | Low | Isaac | Open |
| R-08 | 10 December demonstration slips | Schedule | 3 | 4 | 12 | Medium | Scrum Master (proposed) | Open |
| R-09 | Team capacity or reviewer absence | Schedule | 3 | 3 | 9 | Medium | Scrum Master (proposed) | Open |
| R-10 | Seed, API and database contracts diverge | Technical | 3 | 3 | 9 | Medium | Germain and Isaac | Open |
| R-11 | Imported schedule applied to wrong market or conditions | Safety | 4 | 4 | 16 | High | Germain | Open |
| R-12 | Reminder mistaken for diagnosis during a critical fault | Safety | 2 | 5 | 10 | Medium | Alice and Elise (proposed) | Open |
| R-13 | Monitoring gaps or simulations misreported as measurements | Quality | 3 | 4 | 12 | Medium | Isaac | Open |

## Responses

- **R-01** · Trigger when conflicting manual, wrong market, or a boundary mismatch. Require model-specific source and exact units. Run RT-01–RT-20 and disable disputed rules. Response if triggered. Hold the affected rule and show Unknown.
- **R-02** · Trigger when overall status or requested skill lacks evidence. Require both approval levels and verify examples and suspension controls. Response if triggered. Suspend or demote the listing while evidence is reviewed.
- **R-03** · Trigger when coordinates in logs or cross-account access succeeds. Use RBAC, TLS and hashed credentials. Redact coordinates and verify retention and launch obligations. Response if triggered. Contain exposure and follow the incident and notification process.
- **R-04** · Trigger when fewer than two mechanics willing to be interviewed. Recruit early using a consent script and retain labelled fixtures for demo. Response if triggered. Report recruitment limits and use fictional profiles.
- **R-05** · Trigger when fewer than five participants or one narrow cohort. Recruit diverse consenting drivers and report the sample and limitations. Response if triggered. Report formative findings with sample size and missing groups.
- **R-06** · Trigger when availability is older than 24 h or timestamp is invalid. Normalize freshness before filtering. Test stale and future updates. Response if triggered. Show Unknown and preserve last valid update time.
- **R-07** · Trigger when wrong origin, boundary behaviour or geospatial data. Test raw distances and limits. Mark neighbourhood and straight-line distances approximate. Response if triggered. Use a confirmed neighbourhood or alternate search origin.
- **R-08** · Trigger when any critical workflow incomplete by the planned freeze. Track MVP workflow status at sprint review and freeze the demo scope. Response if triggered. Rehearse with a known working tagged build.
- **R-09** · Trigger when a critical work item has no active reviewer. Assign owners and reviewers and record decisions in the sprint board. Response if triggered. Reassign open work and replan due dates.
- **R-10** · Trigger when fixture import fails or API status differs from contract. Agree nullable thresholds, service keys and timestamp handling. Add import contract checks to CI. Response if triggered. Pin compatible versions and correct the mapping.
- **R-11** · Trigger when origin or operating conditions are unconfirmed. Require source market, body style, powertrain and use-condition evidence. Response if triggered. Keep manual entry available with Unknown schedule.
- **R-12** · Trigger when users interpret a reminder state as evidence a vehicle is safe. Use task-specific copy and safety routing. Confirm interpretation in usability sessions. Response if triggered. Point the driver to qualified assistance and record a UX defect.
- **R-13** · Trigger when unknown slots or controlled outages mixed into measured report. Track coverage, censoring, environment and experiment labels. Cross-check calculations. Response if triggered. Publish coverage bounds and qualify or rerun the observation.

Risk R-03 refers to the Ghana Data Protection Commission’s guidance for organisations. The team should review the obligations that apply before public deployment or collection of real customer data. [Data Protection Commission Ghana](https://dpc.gov.gh/for-organisations/)

The [CSV](risk-register-v1.csv) carries the same scores, owners, triggers, mitigations and responses for sprint tracking.
