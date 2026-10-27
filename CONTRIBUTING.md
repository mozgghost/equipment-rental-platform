# Contributing

1. Create a short-lived branch: `feature/<issue>-<topic>` or `fix/<issue>-<topic>`.
2. Keep business logic in domain/service modules, not views or serializers.
3. Add or update tests for every business-rule change. PostgreSQL-specific invariants must be tested on PostgreSQL, not SQLite.
4. Run `make test`, `make lint`, and `make frontend-build` where the required tools are installed.
5. Open a pull request with context, design/DB implications, security considerations, and test evidence.
6. Never commit `.env`, production data, payment credentials, or user data.

Use Conventional Commits where practical: `feat:`, `fix:`, `test:`, `docs:`, `refactor:`, `build:`, `ci:`. Main is protected; changes are merged through reviewed pull requests after CI passes.
