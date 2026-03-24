# Deployment runbook

## Pre-checks (before deploy)

- [ ] CI green on merge commit (lint, security, tests, coverage threshold).
- [ ] `CHANGELOG.md` / release notes updated for this version (if tagged release).
- [ ] Migrations reviewed; destructive changes have DBA/owner sign-off.
- [ ] RDS snapshot or maintenance window scheduled if high-risk schema change.
- [ ] Secrets present in target environment: `DJANGO_SECRET_KEY`, `DATABASE_URL`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`, S3/AWS as needed.
- [ ] Image tag immutable: prefer `ghcr.io/<owner>/<repo>:vX.Y.Z` or `:sha-<short>` — not floating `latest` alone in prod.

## Deploy steps (typical Docker + compose on EC2)

1. **Pull image**
   - `docker pull ghcr.io/<OWNER>/<REPO>:vX.Y.Z`
2. **Backup** (if not automated): RDS snapshot or logical dump per `docs/operations/backup-restore-and-dr.md`.
3. **Migrate** (container one-off or entrypoint):
   - `docker compose -f docker-compose.prod.yml run --rm web python manage.py migrate --noinput`
4. **Static/media**: if using S3 + collectstatic in image build, verify bucket policy; if local static, run collectstatic as documented in your image.
5. **Roll containers**
   - `docker compose -f docker-compose.prod.yml up -d`
6. **Post-deploy smoke** (automated or manual):
   - `curl -fsS https://<HOST>/health/live/`
   - `curl -fsS https://<HOST>/health/ready/`
   - GitHub Actions: workflow **Smoke tests** (`workflow_dispatch`) with base URL.

## Post-checks

- [ ] HTTP 200 on health endpoints; no unexpected 5xx on home/login.
- [ ] Error budget: 5xx rate in monitoring within SLO (see monitoring checklist).
- [ ] Audit: confirm application logs show expected startup (no migration errors).
- [ ] Optional: run a single UAT scenario from `docs/go-live-checklist.md` on prod (read-only or test account).

## Failure decision tree

```
migrate failed?
  yes -> STOP; do not route traffic to new tasks; restore DB from snapshot if partial apply; see rollback-runbook
  no -> continue

health/ready 503?
  yes -> DB connectivity or settings; check RDS security group, DATABASE_URL, secrets
  no -> continue

5xx spike after cutover?
  yes -> rollback application to previous image tag; keep DB unless migration incompatible
  no -> monitor 24h plan (post-release-verification.md)
```

## References

- `RELEASE.md` — tagging and RC process  
- `docs/runbooks/rollback-runbook.md`  
- `docker-compose.prod.yml` — prod stack shape  
