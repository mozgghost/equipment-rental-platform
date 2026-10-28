# ADR-003: Same-origin session authentication

- **Status:** accepted for the first same-origin browser app.
- **Decision:** Django session cookies with `HttpOnly`, `SameSite=Lax`, CSRF protection on unsafe methods, secure cookies and HTTPS redirect in production.
- **Alternative:** JWT bearer tokens.
- **Trade-off:** CSRF tokens and same-origin deployment need configuration, but the browser does not need to store long-lived bearer tokens in local storage.
- **Follow-up:** email verification, reset flow, session rotation, login rate limiting and production mail provider remain launch blockers.
