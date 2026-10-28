# Project status ledger

**As of:** 2026-10-27

## Confirmed workspace facts

- Project repository: `equipment-rental-platform`; source is present in the local working directory.
- Verified local toolchain: Python 3.13.7, Node.js 22.22.2, npm 10.9.7, Docker CLI 29.5.3 and Docker Compose 5.1.4.
- Backend dependencies are installed in the local virtual environment; `pip check` reported no broken requirements.
- The root `.env` is ignored by Git. `.env.example` is intended for version control.
- The local Compose stack is running. The backend is exposed on host port `8001` because another local project already uses port `8000`. Nginx is exposed on port `8080`.
- No Git commit or push has been performed as part of this verification. CI workflow execution and production deployment have not been verified or performed.

## Implemented in source

- Modular-monolith Django configuration, session/CSRF authentication scaffold, environment-based settings, health/readiness routes and request correlation IDs.
- Custom email-identity account model and owner/manager company membership model.
- Catalogue, category, location, attribute-value, equipment-photo-key and rate-history models, plus public catalogue filters/search/pagination.
- Decimal-only price quotation, immutable quote fields on bookings, idempotency fingerprint, booking/cancellation/hold-expiry services and Celery expiry task.
- Shared `AvailabilityBlock` model for booking and maintenance with a PostgreSQL exclusion constraint. The initial booking migration enables `btree_gist` before creating the constraint.
- Payment/refund/webhook event schemas; real payment processing is disabled and no card data is stored.
- Review, complaint, transactional-outbox and audit event schemas.
- React/TypeScript single-page catalogue shell with same-origin API client, CSRF header behavior and build-time configurable product branding.
- Deterministic sandbox seed command targeting 20 companies, 300 users, 500 equipment items, 50 categories, 200 attributes, 1,000 bookings, 800 synthetic payment rows and 500 reviews. The command exists in source; exact counts and rerun behavior have not been independently verified in this session.
- Architecture, data model, role matrix, threat model, test strategy, API overview/OpenAPI draft, launch/monetization research and Ukrainian course-report outline.

## Verification ledger

| Check | State | Evidence / limitation |
|---|---|---|
| Python syntax compilation | Passed previously | `python -m compileall -q backend` completed successfully. |
| Backend dependency consistency | Passed | `pip check` reported no broken requirements in the local backend environment. |
| Django system check | Passed | `docker compose run --rm backend python manage.py check`: no issues. |
| Initial migrations | Passed | Initial migrations exist for accounts, audit, organizations, inventory, bookings, operations and payments; `showmigrations` reported all migrations applied. |
| Migration drift check | Passed | `docker compose run --rm backend python manage.py makemigrations --check --dry-run`: no changes detected. |
| PostgreSQL range extension | Passed | `btree_gist` extension was present in PostgreSQL. |
| Backend test suite | Passed with warning | `docker compose run --rm backend python -m pytest -q`: 14 passed. One Django deprecation warning remains for `EMAIL_BACKEND`. |
| Frontend typecheck | Passed | `npm run typecheck` completed successfully. |
| Frontend production build | Passed | `npm run build` completed successfully. |
| Compose configuration | Passed | `docker compose config --quiet` completed successfully after the host-port change. |
| Docker Compose runtime | Passed for local smoke test | Seven services are running; PostgreSQL, Redis, backend and frontend report healthy where healthchecks are configured. |
| HTTP smoke tests | Passed | `http://localhost:8080/`, `http://localhost:8001/healthz` and `http://localhost:8080/api/schema/` each returned HTTP 200. |
| OpenAPI generation | Served, with warnings | Schema endpoint returned 200, but several APIViews lack inferred serializers and operationId collisions were logged. |
| Celery worker and Beat | Started | Worker connected to Redis and registered `apps.bookings.tasks.expire_unpaid_booking_holds`; Beat started. Task execution itself has not been verified here. |
| CI workflow | Not verified | No successful GitHub Actions run has been observed. |
| Production deployment | Not done | Local Compose verification is not a production deployment. |
| Seed count/idempotency | Not verified | Run against a disposable database and verify exact counts and rerun behavior before relying on it. |

## Current launch blockers

1. Complete and review authentication/session edge cases, rate limits and audit coverage with runtime tests.
2. Implement email verification, password reset and a production email provider before production account onboarding.
3. Complete tenant-scoped company/equipment write APIs, membership administration and role-specific object permissions with cross-tenant regression tests.
4. Complete handover/return workflow, customer support/complaint/review write and moderation flows, reports and booking-list pagination.
5. Improve OpenAPI schema annotations for APIViews and resolve duplicate operation IDs; verify the generated schema.
6. Investigate the Gunicorn control-server permission warning in the container logs.
7. Verify the seed command's exact counts and idempotency on a disposable PostgreSQL database.
8. Run CI, dependency/image security scans, backup restoration, load tests and the production checklist.
9. If real payments are desired, choose an appropriate provider, implement signed webhook processing, reconciliation and refunds, and obtain legal/provider approval. Keep payment processing disabled until tested.

## Important status semantics

- **Implemented** means source files exist.
- **Checked** means the listed command completed successfully.
- **Locally running** means the local Compose services started and the specified smoke checks passed.
- **Deployed** means a real deployment was performed and verified; this project has not been deployed.
