# API overview

Base path: `/api/`; authentication is Django session-cookie auth. For write methods, first call `GET /api/auth/csrf/` and pass the `csrftoken` cookie as `X-CSRFToken`. This client uses same-origin cookies; do not store long-lived access tokens in local storage.

## Auth

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/auth/csrf/` | Establish CSRF token cookie. |
| POST | `/api/auth/register/` | Create account; email-verification flow is still incomplete. |
| POST | `/api/auth/login/` | Create session. |
| POST | `/api/auth/logout/` | End session; authenticated and CSRF-protected. |
| GET | `/api/auth/me/` | Current user profile and company memberships. |

## Catalogue

| Method | Path | Purpose | Query support |
|---|---|---|---|
| GET | `/api/catalog/categories/` | Active category list. | None. |
| GET | `/api/catalog/equipment/` | Published listings, page-number paginated. | `search`, `category`, `location__city`, `location__country_code`, `billing_unit`, `min_price`, `max_price`, `ordering`, `available_from`, `available_to`. |
| GET | `/api/catalog/equipment/{slug}/` | Public equipment detail. | Slug. |

`search` searches name/description/company/city. Ordering fields are `base_rate`, `name`, `created_at`. Availability timestamps must be timezone-aware ISO-8601 strings.

## Booking

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/bookings/` | Current renter's bookings and bookings belonging to companies they are members of; currently capped at 100 records and not a full pagination contract. |
| POST | `/api/bookings/` | Create reservation hold; requires `Idempotency-Key`. Body: `equipment_id`, `starts_at`, `ends_at`. Server calculates quote; overlapping active intervals respond with 409. |
| GET | `/api/bookings/{id}/` | View an accessible booking. |
| POST | `/api/bookings/{id}/` | Cancel an eligible future booking; optional `reason` field. |

## Error semantics

- 400: schema/domain validation failed.
- 401/403: authentication/permission or CSRF failure, depending on authentication state.
- 404: resource not found or intentionally hidden by access scope.
- 409: reservation overlap or idempotency-key conflict.
- 5xx: unexpected internal failure; response must not expose tracebacks in production.

This is an early API scaffold. Some routes have only model representation and are not yet implemented: company administration, equipment write APIs, handover/return, complaint/review write/moderation, reports, password reset, email verification and real payment webhooks. OpenAPI can be served at `/api/schema/` after installing dependencies and validating the schema.
