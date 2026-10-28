# Requirement traceability matrix (initial)

| Requirement | Source component | Test evidence required | Documentation | State |
|---|---|---|---|---|
| Public catalogue/search | `apps/inventory/` + frontend | API filter, paging, empty/error cases | `architecture/overview.md`, `api/` | Partial source |
| Company membership | `apps/organizations/models.py` | owner/manager permission matrix and cross-tenant negatives | `security/threat-model.md` | Model only; enforcement incomplete |
| Server-side price | `apps/bookings/domain/pricing.py`, `Booking` snapshot | Decimal rounding, duration boundaries, rate-change invariance | `database/schema.md` | Partial source |
| Prevent double booking | `AvailabilityBlock` exclusion constraint and service | PostgreSQL concurrent overlapping inserts, adjacent boundaries, maintenance collision | `architecture/decisions/ADR-002-shared-availability-table.md` | Design/source; migration/test unverified |
| Idempotency | `create_booking`, unique key + fingerprint | same request replay and changed payload conflict | `test-strategy.md` | Partial source |
| Hold expiry | `expire_unpaid_booking_holds` | expired hold frees block; task retry safe | `operations/runbook.md` | Source only |
| Payment gateway/webhooks | `apps/payments/` | provider test mode, signature and duplicate webhook tests | `security/threat-model.md` | Schema only; disabled |
| Review/moderation | `apps/operations/` | only renter after completed rental; admin moderation | `use-cases.md` | Model only |
| Audit | `apps/audit/` | critical action event tests and scrubbed metadata | `security-checklist.md` | Model/request ID only |
| Seed dataset | `apps/inventory/management/commands/seed_demo_data.py` | exact count and deterministic rerun on disposable PostgreSQL | `database/schema.md` | Implemented in source; not run/verified |
| CI/CD | `.github/workflows/` | actual successful workflow run | `testing/test-results.md` | Workflow template only |
| Ukrainian course report | `docs/university-report/` | verify matches actual implementation/test output | `university-report/outline.md` | Draft outline only |


Access-control note: `accessible_bookings` must include only active memberships. A regression test should verify an inactive member cannot read or cancel a company booking. Runtime API tests have not yet executed in this environment.


Tenant-isolation regression source: `backend/tests/test_api_permissions.py::test_inactive_company_member_cannot_read_or_cancel_company_booking`. The test has been authored but awaits execution with the Django test stack and PostgreSQL.
