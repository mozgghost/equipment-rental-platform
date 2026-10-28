# Test results ledger

**Last updated:** 2026-10-27

| Check | Result | Evidence / caveat |
|---|---|---|
| Python syntax | PASS | `python -m compileall -q backend` completed successfully in the earlier verification pass. |
| Backend dependency consistency | PASS | `pip check` reported no broken requirements. |
| Django system checks | PASS | `docker compose run --rm backend python manage.py check`: no issues. |
| Migration state | PASS | `showmigrations` showed all initial migrations applied for the project apps and Django built-in apps. |
| Migration/model drift | PASS | `docker compose run --rm backend python manage.py makemigrations --check --dry-run`: `No changes detected`. |
| PostgreSQL `btree_gist` extension | PASS | Extension was present in the PostgreSQL database. The bookings initial migration installs it before the exclusion constraint. |
| Full backend test suite | PASS, 14 tests | `docker compose run --rm backend python -m pytest -q`: `14 passed, 1 warning`. The warning is a Django deprecation notice for `EMAIL_BACKEND`, not a test failure. |
| Frontend typecheck | PASS | `npm run typecheck` completed successfully. |
| Frontend production build | PASS | `npm run build` completed successfully; Vite generated the production bundle. |
| Compose configuration | PASS | `docker compose config --quiet` exited successfully. |
| Docker Compose smoke test | PASS | Seven services were running; PostgreSQL, Redis, backend and frontend healthchecks passed where configured. |
| HTTP smoke tests | PASS | Frontend through Nginx: HTTP 200 at `http://localhost:8080/`; backend health: HTTP 200 at `http://localhost:8001/healthz`; API schema through Nginx: HTTP 200 at `http://localhost:8080/api/schema/`. |
| Celery startup | PASS, startup only | Worker connected to Redis and registered the unpaid-booking expiry task; Beat started. Scheduled task execution was not verified. |
| OpenAPI schema | PASS with warnings | Endpoint returned HTTP 200. Schema generation logged missing serializer inference for several APIViews and duplicate operation IDs. |
| Gunicorn logs | NEEDS REVIEW | The backend logged a control-server permission error involving `/nonexistent`; service health and HTTP checks nevertheless passed. Root cause has not been confirmed. |
| Seed count/idempotency | NOT VERIFIED | Exact fixture counts and safe rerun behavior have not been checked against a disposable PostgreSQL database. |
| GitHub Actions CI | NOT VERIFIED | No successful remote workflow run is claimed. |
| Security scans / production deployment | NOT RUN | No external scan or production deployment is claimed. |

## Outstanding verification and quality items

- Improve OpenAPI serializer annotations and remove duplicate operation IDs.
- Investigate the Gunicorn control-server permission warning.
- Migrate away from the deprecated `EMAIL_BACKEND` setting before the applicable Django deprecation deadline.
- Verify seed counts and idempotency on a disposable PostgreSQL database.
- Run CI and the remaining security, backup-restore, load and production-readiness checks.
