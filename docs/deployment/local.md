# Local development

1. Install Python 3.13+, Node.js 22+, Docker Engine and Compose plugin.
2. Copy `.env.example` to `.env`; change `DJANGO_SECRET_KEY` and `DB_PASSWORD`. Keep `.env` out of Git.
3. Run `docker compose up --build`.
4. Generate/review migrations on the active branch, then `docker compose exec backend python manage.py migrate`.
5. Create a local staff account with `createsuperuser`. Do not use production credentials for development.
6. Run backend unit/integration tests against a dedicated test DB.

The package as delivered may require migration generation and frontend lockfile creation before the full workflow works end-to-end. See status ledger.
