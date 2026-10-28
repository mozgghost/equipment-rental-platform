# ADR-001: Modular monolith

- **Status:** accepted for MVP.
- **Context:** one small product team needs transactional booking consistency and maintainable domain boundaries.
- **Decision:** Django modular monolith, split by business domain; React client; PostgreSQL source of truth.
- **Alternatives:** microservices or serverless functions.
- **Trade-off:** deployment is less independently scalable by module, but transactions and local development remain substantially simpler.
- **Revisit when:** measured load, release coupling, or multiple autonomous teams justify extraction.
