# Equipment Rental Platform

B2B marketplace foundation for renting construction and specialist equipment. This is an **early development scaffold**, not a production release. The initial focus is on a searchable equipment catalogue, company-scoped access, server-side quotes, and a PostgreSQL-backed reservation invariant.

## Status at a glance

- **Implemented in source:** initial Django domain models, Decimal pricing function, session-auth API scaffold, catalogue endpoints, booking service, PostgreSQL exclusion constraint design, Celery task for expiry, responsive React shell.
- **Verified locally:** initial migrations applied, Django checks and migration drift check passed, 14 backend tests passed, frontend typecheck and production build passed, and the Docker Compose stack started. Frontend, backend health and API schema smoke checks returned HTTP 200. See `docs/PROJECT_STATUS.md` for evidence and remaining limitations.
- **Disabled by design:** real payments and AI integrations.

See [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) for the precise status ledger and known blockers.

Set `VITE_APP_NAME` in the root `.env` to configure the visible React brand and browser title; `APP_NAME` also names the API in its generated documentation.

Create a deterministic source archive from the project root with `python scripts/package_project.py`; the script excludes local environment files, credentials, caches, virtual environments, installed frontend dependencies and build artifacts.

## MVP scope

1. Public catalogue and filters.
2. Email-identity account scaffold and session authentication with CSRF.
3. Company membership and role model.
4. Server-side booking quote snapshot and idempotency key.
5. Shared availability-block table for bookings and maintenance periods.
6. Operational models, audit-event model, OpenAPI scaffold, Docker and CI templates.
7. Sandbox seed command for the specified sample counts (source exists; database execution still needs verification).

## Architecture

A modular monolith: Django/DRF backend, React/TypeScript frontend, PostgreSQL as the source of truth, Redis/Celery for expiry and durable asynchronous work, reverse proxy at the edge. No microservices are required for the initial product.

## Local quick start

Requirements: Python 3.13+, Node.js 22+, npm, Docker Engine with Compose plugin. Install Docker first if absent.

```bash
cp .env.example .env
# Edit DJANGO_SECRET_KEY and DB_PASSWORD for your local machine.
docker compose up --build
```

The initial migrations have already been generated, reviewed for the `btree_gist` extension ordering, applied to the local Compose database, and checked for model drift. For future model changes, generate and review new migrations, then run the migration checks and tests before committing.

```bash
docker compose exec backend python manage.py showmigrations
docker compose exec backend python manage.py createsuperuser
```

With Compose, open the application at `http://localhost:8080`; the API is routed through `/api/`, schema at `/api/schema/` and Swagger UI at `/api/docs/`. The backend is also exposed on `http://localhost:8001` for local tools. Host port `8000` may be used by another local project; the container continues to listen internally on port `8000`. To use Vite hot reload, install frontend dependencies on the host and run `cd frontend && npm run dev`. Check `frontend/vite.config.ts` for the configured API proxy target; the backend host port in this workspace is `8001`. The Docker Compose stack was started and verified locally: the frontend, backend health endpoint, and API schema returned HTTP 200.

To create the deterministic local sandbox fixture set after migrations, run `make seed` (or `docker compose exec backend python manage.py seed_demo_data --seed 20261026 --allow-sandbox`). The command requires `DJANGO_DEBUG=1`, an explicit `--allow-sandbox` flag and a local database host; it produces only synthetic `.example.test` accounts and demo payment rows, and creates unusable passwords for seeded users. It is not a payment simulator. Exact fixture counts and rerun behavior still need verification on a disposable PostgreSQL database.

## Repo map

- `backend/apps/`: Django domain modules.
- `frontend/`: React/TypeScript client.
- `infrastructure/`: reverse proxy and monitoring templates.
- `scripts/`: deterministic packaging utility.
- `docs/`: architecture, security, testing, operations and university-report materials.
- `tests/`: integration, E2E and load-test plans/suites.

## Engineering rules

- Money uses `Decimal`, never binary `float`.
- All timestamps are timezone-aware; rental intervals are half-open `[start, end)`.
- Client-supplied price is never authoritative.
- Tenant checks are enforced on the backend.
- Payment/webhook success is provider-authoritative; the current payment mode is disabled.
- PostgreSQL, not SQLite, is required for the range exclusion invariant.
- No claim of production readiness until the acceptance checks in `docs/requirements/traceability.md` pass.
