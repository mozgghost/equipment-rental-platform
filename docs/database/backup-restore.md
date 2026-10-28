# Backup and restore plan

## Minimum production policy (to be agreed with an operator)

- Automated encrypted daily base backups plus WAL/PITR if the selected hosting plan supports it.
- Define recovery point objective (RPO) and recovery time objective (RTO) with business stakeholders before production; do not assume zero data loss.
- Keep copies in a separate account/region from the primary DB and restrict restore access.
- Test restore at least quarterly and after major database changes; record restore duration and integrity checks.
- Exclude secrets from dumps and use encrypted secret management for credentials.

## Example manual logical backup

```bash
pg_dump --format=custom --no-owner --no-acl "$DATABASE_URL" > backup.dump
pg_restore --list backup.dump
# Restore only into a new, isolated database first; validate before swapping traffic.
```

The exact production commands depend on the managed database provider and are not executed by this project scaffold. Never restore production data into an automated-test database.
