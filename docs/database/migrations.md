# Migration strategy

1. Generate migrations from the current model state using the pinned Django version; review every generated diff.
2. Ensure PostgreSQL `btree_gist` is enabled **before** creating the range exclusion constraint (Django `BtreeGistExtension` operation).
3. Deploy additive changes first; backfill data; only then make fields non-null or remove obsolete columns.
4. Back up before migrations that rewrite large tables. Test both upgrade and rollback strategy on a restored staging copy.
5. Never edit an already-applied migration in a shared environment; add a follow-up migration.
6. CI test database must be PostgreSQL and have extension creation privileges required by migration.

Migrations are a blocking deliverable until generated and exercised against PostgreSQL. No claim is made that they are ready in this source tranche.
