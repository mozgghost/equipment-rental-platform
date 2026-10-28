# Security checklist before pilot

- [ ] Secret scan on repository history and final archive.
- [ ] Production secret key, unique DB credentials and private secret store.
- [ ] HTTPS, trusted hosts, correct proxy headers, HSTS rollout and secure cookies.
- [ ] Review CSRF and session lifecycle; test login throttling/lockout policy.
- [ ] Email verification and secure single-use password-reset tokens.
- [ ] Object-level authorization tests across every company-owned resource and export.
- [ ] Prove manager cannot change owner role or edit other company's data.
- [ ] PostgreSQL `btree_gist` exclusion constraint migration and race tests.
- [ ] Upload MIME/signature/size limits, malware scan and object-store ACLs.
- [ ] Webhook signature/idempotency tests before any real PSP activation.
- [ ] Ensure logs/metrics do not contain raw emails, tokens, payment payloads or precise addresses unnecessarily.
- [ ] Dependency, container and SAST scans; review findings.
- [ ] Backups encrypted; restore tested and documented.
- [ ] Admin actions require explicit privileges and create audit records.
- [ ] Incident contact, response ownership and security disclosure process configured.
