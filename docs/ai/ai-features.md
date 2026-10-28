# AI features and safety boundary

AI integration is disabled by default (`AI_FEATURES_ENABLED=0`) and is not required for search or booking.

## Roadmap

1. Natural-language query → structured catalogue filters. Keep price, date availability, tenant scope and equipment state deterministic.
2. Recommendations based on the authorized catalogue and observable user filters; explain the matching attributes.
3. Popularity analysis from aggregate booking events after sufficient clean data exists.
4. Demand forecasting only after historical seasonality and data-quality checks. Until then, show descriptive statistics rather than a fabricated confidence score.
5. Tariff recommendations as decision support; human company owner confirms changes. Never edit existing booking snapshots.

Controls: send only fields the user is allowed to see; do not send secrets or other-company private reports; treat catalogue descriptions as untrusted prompt content; validate structured outputs; apply API cost/timeout limits; log model/version and latency without logging confidential prompts; provide a kill switch. LLM output never confirms availability, changes permissions, sets a final price or approves payment.
