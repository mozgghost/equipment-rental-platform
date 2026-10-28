# Threat model (initial)

## Assets

Business customer identity and contact data; company isolation; inventory/pricing; rental dates; financial records; uploaded equipment imagery; moderation/audit records; credentials and provider secrets.

## Trust boundaries

Browser ↔ reverse proxy/API; user ↔ organization; application ↔ PostgreSQL; application ↔ Redis/worker; platform ↔ email/PSP/LLM providers; uploaded file ↔ storage/processing pipeline.

## Top risks and controls

- **BOLA/IDOR / cross-tenant data:** build every company query from authenticated membership; use object-level permission checks; negative tests for cross-company GET/PATCH/DELETE/export. Frontend visibility is never authorization.
- **Double booking/races:** DB exclusion constraint on a shared allocation table; transaction and row lock; idempotency; concurrent PostgreSQL tests.
- **Payment replay/forgery:** disabled by default; later validate signatures against raw body, deduplicate provider/event IDs, verify amount/currency/connected account and reconcile; never trust redirect return.
- **XSS/unsafe media:** escape output; restrict file size/MIME and decode/re-encode images; store opaque object keys, scan files, no inline arbitrary HTML.
- **CSRF/session theft:** same-origin session cookie, `HttpOnly`, `SameSite`, secure cookies on HTTPS, CSRF token on unsafe routes and session rotation.
- **Credential abuse:** strong password validation, throttling, generic auth error, mail verification, reset flow, MFA for platform admins recommended before launch.
- **Secrets/log leaks:** environment/secret manager; scrub request bodies, tokens, card-like values and personal data from logs.
- **SSRF/injection:** no remote URL fetch in MVP; parameterized ORM; if remote import/image URL is later added, deny internal IP ranges and enforce allowlists/timeouts.
- **AI prompt injection/data leakage:** AI disabled; future prompts use only authorized catalogue facts, no secrets or other-tenant data, model output is never an authority for price/availability/permissions.
- **Infrastructure/dependencies:** pin dependencies, scan source/image, use non-root images and least-privilege DB user, patch cadence and tested backups.

## Residual risks

This is a design-time threat model, not a completed penetration test. Tenant-specific mutation APIs, mail workflows, media processing, payment webhook handling and production configuration are unfinished.
