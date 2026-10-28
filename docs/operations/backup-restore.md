# Backup and restore operations

Use the procedure in `docs/database/backup-restore.md`, but execute restores only in an isolated environment first. Validate row counts, migration version, foreign key integrity and a booking availability sample. Record start/end time, backup point, operator and observed RPO/RTO. Never test a restore by overwriting the live database.
