# Use cases

## Renter

1. Browse and filter public equipment.
2. Select timezone-aware start and end timestamps.
3. Request a server quote and booking; server recalculates from the current tariff and snapshots the agreed amounts.
4. See current status and cancel a permitted future reservation.
5. Later: payment, handover documents, return, review and support request.

## Company manager

1. Create/edit equipment in their own company.
2. Manage tariffs, photos and locations.
3. Accept/book handling, record handover/return, schedule maintenance.
4. View company-scoped operational data.

## Company owner

All operational manager capabilities plus membership/role administration, company configuration and authorized reporting. A user cannot change their own role to owner through a client-supplied field.

## Platform admin

Manage categories, company/user moderation, complaints, review moderation, audit and policy settings. High-impact actions must capture actor, reason, target and timestamp.

## Failure cases

- no matching equipment → empty state, not 500;
- invalid or naive timestamps → 400;
- simultaneous overlap → 409;
- duplicate idempotency key with same payload → same booking result;
- duplicate key with changed payload → 409;
- tenant mismatch → 404/403 with no data disclosure;
- payment provider unavailable → do not mark successful; use retry/reconciliation.
