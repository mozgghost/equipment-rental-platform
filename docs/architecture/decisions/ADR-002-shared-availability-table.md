# ADR-002: One availability-block table

- **Status:** accepted; must be validated by PostgreSQL migration and concurrency tests.
- **Context:** reservations and maintenance must not overlap for the same physical unit. PostgreSQL exclusion constraints are table-local and cannot compare rows across two separate tables.
- **Decision:** represent both reservation and maintenance allocations in `AvailabilityBlock`, with a range field and an exactly-one-source check; add a conditional GiST exclusion constraint on equipment equality and range overlap for active blocks.
- **Alternative:** lock equipment rows and run all conflict checks in a carefully designed serializable transaction.
- **Trade-off:** one table contains two source types, but the invariant is enforced by the database. Releasing a block is an explicit state change; rows are not physically deleted.
- **Risks:** extension/constraint migration ordering, booking state/block consistency, and unsupported local SQLite tests.
