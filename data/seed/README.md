# Seed data

The seed loader (`make seed`, see [docs/data/schema.md](../../docs/data/schema.md#loading-the-seed-make-seed)) expects these three files from Germain and Isaac's Sprint 1 package (#41):

- `vehicles.json`: vehicle catalogue
- `maintenance_rules.json`: reminder rules, applicability and sources
- `mechanics.json`: **fictional** demo mechanics, service categories and neighbourhoods. Loaded only when `DEMO_MODE=true`.

Edit these files through PRs. The loader validates them and rejects a broken seed without writing anything.
