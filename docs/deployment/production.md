# Production deployment plan (not executed)

## Recommended topology

Managed PostgreSQL in a chosen data region; application containers in a private network; object storage for images; Redis only if the selected worker workflow is enabled; reverse proxy/TLS at managed ingress or Nginx; centralized logs/metrics; transactional email provider. Choose a provider only after region, GDPR/data-processing, budget and support requirements are known.

## Release sequence

1. Create isolated staging environment with production-like PostgreSQL version.
2. Store secrets in secret manager; use a minimally privileged DB role.
3. Build immutable images from a tagged commit and scan dependencies/images.
4. Apply backwards-compatible migrations; run smoke checks and critical E2E tests.
5. Verify health/readiness, login, company isolation, catalog, booking conflict and rollback drill.
6. Release behind restricted access to pilot users; enable public access only after checklist approval.
7. Monitor and rollback to previous immutable image if error/latency thresholds trip. Do not reverse migrations blindly where data loss is possible.

Real payments, public launch and DNS cutover have not been executed or approved by this scaffold.
