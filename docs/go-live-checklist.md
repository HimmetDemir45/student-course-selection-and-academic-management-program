# Go-live checklist (UAT + technical + operations)

## UAT scenarios (business)

- [ ] **Student enrollment**: browse sections → enroll → capacity / prerequisite / conflict messages as expected.
- [ ] **Drop / withdraw**: within add-drop window; audit log entry if applicable.
- [ ] **Instructor grading**: grade entry for own section only; forbidden for other sections.
- [ ] **Transcript / GPA**: completed courses + letter grades match expected calculation.
- [ ] **RBAC**: student cannot open admin dashboard; admin can CRUD departments/announcements as designed.
- [ ] **Auth**: login, logout, password reset mail (or console in staging).

## Technical (pre go-live)

- [ ] **Env**: `DJANGO_SETTINGS_MODULE=config.settings.prod`, `DEBUG=False`, secrets only in vault/env on server.
- [ ] **Migrations**: `showmigrations` matches expected; dry-run on staging already done.
- [ ] **Static / media**: S3 URLs load; `collectstatic` path correct for prod image.
- [ ] **Health**: `/health/live/`, `/health/ready/` return 200 from public URL.
- [ ] **TLS**: valid certificate; `DJANGO_CSRF_TRUSTED_ORIGINS` matches site URL.
- [ ] **CI**: last `main` build green; release tag built if using SemVer release.
- [ ] **Alerts**: SNS/Slack/email route tested with a synthetic alarm.

## Operations

- [ ] **Support owner**: name + contact for launch day.
- [ ] **Rollback owner**: who can run `rollback-runbook.md` steps.
- [ ] **Communication**: short “maintenance / launch” text for users/stakeholders (copy below).

### Release communication (template)

```
[Baslik] Sistem guncellemesi tamamlandi
[Metin] Ders secimi ve akademik yonetim portalı yeni surume guncellendi.
Sorun yasarsaniz <destek kanali> uzerinden iletisime gecin.
```

## Sign-off

| Role | Name | Date | Signature / note |
|------|------|------|------------------|
| Product / course owner | | | |
| Engineering | | | |
| Ops / infra | | | |
