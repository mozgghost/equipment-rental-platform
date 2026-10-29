# Monitoring integration status

Prometheus and Grafana are planned, but exporters, dashboards and alert rules are not yet wired into Compose. The application currently exposes `/healthz` (process response) and `/readyz` (database readiness). These endpoints intentionally return no connection strings or credentials.

## Next implementation step

Add bounded-cardinality application metrics via a maintained Django Prometheus integration or a custom, reviewed middleware: request count/latency/error status, booking conflicts, booking create success/failure, payment reconciliation failures (after integration), and Celery task failure/queue age. Never use user IDs, booking IDs, emails, raw paths with IDs, payloads or provider tokens as metric labels.

Prometheus must be private; Grafana authentication and access controls are required. Production deployment must choose retention, alert owners and thresholds based on observed baselines.
