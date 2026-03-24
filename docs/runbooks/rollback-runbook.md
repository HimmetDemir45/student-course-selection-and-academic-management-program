# Rollback runbook

## Application rollback (fast)

**Goal**: restore previous known-good container image without data loss when migrations are compatible.

1. Identify last good tag: e.g. `sha-<commit>` or `vX.Y.(Z-1)` from GHCR history.
2. On host:
   ```bash
   docker pull ghcr.io/<OWNER>/<REPO>:<previous-tag>
   ```
3. Update compose/env to pin that tag (avoid `latest` drift).
4. `docker compose -f docker-compose.prod.yml up -d`
5. Verify:
   - `/health/live/`, `/health/ready/`
   - Smoke workflow or manual curls on login + home.

**Note**: Rolling back **code** does not undo DB schema if a new migration already ran.

## Database / migration rollback

- **Forward-only migrations** are normal in Django. Reversing production schema is risky.
- If a migration must be undone:
  - Prefer **restore RDS snapshot** taken **before** the bad deploy (RPO trade-off).
  - Only use `migrate <app> <previous_migration_name>` if the team has tested reverse migrations and no data loss.
- **Irreversible migrations** (data deletes, column drops): snapshot restore is often the only safe path.

## Rollback after failed release workflow

- GitHub Actions **Release** run prints a **rollback-hint** summary when CI, image push, or remote smoke fails.
- Do not promote a broken tag to prod; fix forward on `main` and cut `vX.Y.(Z+1)` or hotfix per `docs/post-release-verification.md`.

## Post-rollback validation

- [ ] Health endpoints OK.
- [ ] Login works (smoke account).
- [ ] Critical read paths: course list, enrollment browse (student test user).
- [ ] Monitoring: error rate returns to baseline within agreed window.
- [ ] Incident ticket updated with what was rolled back and why.
