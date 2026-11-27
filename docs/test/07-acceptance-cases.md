# Acceptance test cases: US-01, US-02, US-04
**Nkenten AutoCare · Sprint 3 · Isaac · 24 November 2026**

One case per acceptance criterion, taken word for word from the story issues (#53, #54, #55). These cases are run in the browser for P3-20 (#85). Record each run in the results table at the end.

## Test data

| Item | Value |
|---|---|
| New driver | `ama.test+<run>@example.com`, phone `+233 20 000 0001`, password `Demo-pass-2026` |
| Existing driver | `existing.driver@example.com`, already registered before the run |
| Catalogue car | 2014 Toyota Corolla, petrol, sedan (catalogue `V01`, the persona's car). `V01` has no supported rules (`rules_supported: false`). **This depends on P1-10 (#32), which is still open. Update this row if #32 picks a different car.** |
| Manual car | 2016 Nissan Almera, petrol (not in the catalogue) |
| Odometer | 142,000 km at registration |
| Time zone | Africa/Accra (UTC+0); "today" means the local date |

## US-01 · Sign up (#53)

| ID | Given | When | Then (pass if all hold) |
|---|---|---|---|
| AT-US01-1 | I'm a new driver on the Sign up screen with valid details | I submit the form | I'm logged in without a separate login step · I land on the garage screen · it shows the empty state with no vehicles · reloading the page keeps me logged in |
| AT-US01-2 | An account with `existing.driver@example.com` already exists | I sign up again with that email | The message reads exactly "An account with this email exists," · I'm not logged in · no second account exists (logging in as the existing driver shows their original garage; the API returned `409 account_exists`) |

## US-02 · Register vehicle (#54)

| ID | Given | When | Then (pass if all hold) |
|---|---|---|---|
| AT-US02-1 | I'm logged in, and the 2014 Corolla petrol sedan is in the catalogue (`V01`) | I enter its make, model, year, powertrain and odometer, then save | The car appears in my garage · it's linked to catalogue `V01` (the API response has `catalogue_id: "V01"`) · because `V01` has no supported rules, no rule activates and each reminder shows "Schedule unknown" with a manual or mechanic link (rule spec, RT-12), never a guessed schedule |
| AT-US02-2 | I'm logged in, and a 2016 Nissan Almera isn't in the catalogue | I enter it and save | The car is saved and appears in my garage · it's marked as manual (`catalogue_id` is null) · I'm told reminders may be limited |
| AT-US02-3a | I'm on the Register vehicle form | I enter an odometer of `-5` and press save | Save is blocked · a message explains the odometer can't be negative · no vehicle is created |
| AT-US02-3b | I'm on the Register vehicle form | I leave the odometer blank and press save | Save is blocked · a message asks for the odometer reading · no vehicle is created |

## US-04 · Log service (#55)

Before these cases, register the catalogue car (2014 Corolla) and log one earlier service: oil and filter, 1 Jun 2026, 135,000 km.

| ID | Given | When | Then (pass if all hold) |
|---|---|---|---|
| AT-US04-1 | I have a saved car with one logged service | I log an oil and filter service dated today at 142,000 km, with a note | Both services appear in the history, **newest first** · the new entry shows date, mileage, type and note as entered |
| AT-US04-2 | The car's latest logged mileage is 142,000 km | I log a service at 140,000 km | Before saving, I'm asked to confirm the lower mileage · **cancel:** nothing is saved · **confirm:** the service is saved (the API returned `409 odometer_lower_than_latest`, then accepted with `confirm_lower: true`) |
| AT-US04-3 | I have a saved car | I log a service dated tomorrow | Save is blocked with a message · nothing is saved (the API returned `400 future_date`) · *boundary:* a service dated today is accepted |

## Open questions (confirm before the #85 run)

1. **US-01, phone sign-up:** the story allows phone or email, but the criteria only cover a duplicate *email*. Is a duplicate *phone* also blocked, and with what message? (Alice and Elise)
2. **US-02, catalogue car without rules:** the test car (2014 Corolla, `V01`) is in the catalogue but has no supported rules. AT-US02-1 therefore expects "Schedule unknown", as the rule spec requires, rather than active reminders. That means the positive path, a car whose rules do activate (e.g. a 2023–2025 Corolla, `V03`), isn't covered in the browser. Should we add one extra case for it, or confirm in #32 that the demo stays on the 2014 car? (Alice, Elise and Henry)
3. **US-04, lower mileage:** the story says confirm, but the rule spec (RT-14) says reject rollbacks. The API contract follows the story (`confirm_lower`). The test follows the story; the conflict is listed on #68.

## Results

| ID | Date | Build | Result | Evidence | Defect |
|---|---|---|---|---|---|
| AT-US01-1 | | | | | |
| AT-US01-2 | | | | | |
| AT-US02-1 | | | | | |
| AT-US02-2 | | | | | |
| AT-US02-3a | | | | | |
| AT-US02-3b | | | | | |
| AT-US04-1 | | | | | |
| AT-US04-2 | | | | | |
| AT-US04-3 | | | | | |
