# Test strategy

## Test layers

- **Unit:** pure Decimal pricing, interval validation, transition policy and statistics.
- **Integration:** DRF endpoints, PostgreSQL schema/constraints, transaction rollback, outbox and scheduled expiry.
- **Authorization/security:** direct object IDs from another company, role escalation, suspended users, unauthenticated mutation, mass assignment and sensitive-field exposure.
- **Concurrency:** simultaneous overlapping creates for the same equipment; assert exactly one succeeds for overlapping intervals, adjacent half-open intervals can both succeed, no active block overlaps maintenance, and identical idempotent retry does not duplicate a booking.
- **E2E:** catalogue → sign in → book → confirm in test mode → cancel; company user creates listing and maintenance; admin moderates complaint.
- **Load:** define data seed and p50/p95/p99/error-rate thresholds, then measure under PostgreSQL/Redis resource limits. Never publish latency/SLA claims before recording a reproducible run.

## Environment requirements

PostgreSQL matching the target major version is required for the exclusion constraint and concurrency suite. SQLite is not accepted as evidence for this invariant. Production data is never used by tests. Every test run should use a disposable database with restricted credentials.

## Current evidence

See `test-results.md`. Model/API tests and concurrency tests remain incomplete until dependencies, migrations and PostgreSQL are available.
