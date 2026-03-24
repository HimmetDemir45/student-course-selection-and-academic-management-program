# Backup, restore, and disaster recovery (DR)

> Placeholder targets — replace with your org’s SLAs.

## RPO / RTO (example placeholders)

| Asset | RPO (max data loss) | RTO (time to restore service) |
|-------|---------------------|-------------------------------|
| RDS (MySQL) | 24 h (daily snapshot) | 1–4 h (manual restore + verify) |
| S3 static/media | Versioning + cross-region optional | 1–2 h |
| Application config (secrets) | 0 (re-enter from vault) | < 1 h |

## RDS (MySQL)

- **Policy**: enable **automated backups**; retention ≥ 7 days (production); align with compliance.
- **Manual snapshot**: before major migrations or risky releases (see deployment runbook).
- **Restore test**: quarterly restore to a **non-prod** instance; run `migrate` status check and read-only queries against critical tables (students, enrollments).

### Restore outline (staging first)

1. Create new RDS instance from snapshot (or restore to point-in-time).
2. Update **staging** `DATABASE_URL`; run smoke tests.
3. For prod cutover: maintenance window, update secrets, restart app, validate health + UAT subset.

## S3 (static / media)

- Enable **versioning** on buckets serving user or irreplaceable media.
- Lifecycle rules for old versions (cost vs retention).
- Cross-region replication optional for DR.

## Backup verification routine

- [ ] Monthly: confirm last automated snapshot exists and is restorable (AWS console or CLI).
- [ ] Quarterly: full restore drill to staging documented with date + owner.

## Application / secrets

- No DB backup replaces **secrets rotation** if leaked — see `SECURITY.md`.
- Export of `.env` files must **not** be stored in git; use AWS Secrets Manager / SSM Parameter Store patterns.

## DR scenario (region loss)

1. Stand up RDS restore in secondary region (if multi-region strategy exists).
2. Point DNS / ALB to new region or failover pattern per AWS architecture.
3. Redeploy containers with same image tag + env.

This repo documents process; implementation is infrastructure-specific.
