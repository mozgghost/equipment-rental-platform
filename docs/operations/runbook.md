# Operations runbook (initial)

## Incident triage

1. Identify scope by timestamp, request ID and service health.
2. Check API 5xx rate, latency, DB connections, worker queue and failed tasks.
3. Do not paste credentials or full user/payment payloads into issues.
4. For booking conflict spikes, inspect exclusion-constraint errors by request ID; distinguish expected 409 conflicts from unexpected DB failures.
5. For payment anomalies (when integration is later enabled), pause payment capture, reconcile against provider events, and never manually mark a payment successful without provider-authoritative evidence.
6. Restore service from a known image/config; follow backup/restore runbook for data incidents.

Alert thresholds, on-call ownership, exact dashboards and contact escalation are not configured yet.
