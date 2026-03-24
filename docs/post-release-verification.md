# Post-release verification (first 24 hours)

## Checkpoints

| When | Actions |
|------|---------|
| **T+15 min** | Health endpoints; 5xx rate; error logs; login smoke; `X-Request-ID` visible on a sample response |
| **T+1 h** | RDS connections, CPU; ALB target health; enrollment smoke (staging or prod test account) |
| **T+4 h** | Compare error budget to baseline; review slow query log if enabled |
| **T+24 h** | Full smoke workflow; confirm backups/snapshots ran; close release ticket or open follow-ups |

## Known issues & watchlist

Maintain a short list after each release:

| ID | Symptom | Severity | Owner | ETA |
|----|---------|----------|-------|-----|
| | | | | |

## Hotfix process

1. Branch from tag or `main`: `hotfix/vX.Y.(Z+1)-description`
2. Minimal change + targeted test (`manage.py test` subset or full CI).
3. PR with expedited review (CODEOWNERS / instructor approval).
4. Merge → tag `vX.Y.Z` → **Release** workflow or manual image build.
5. Deploy using `deployment-runbook.md`; monitor T+15 min again.
6. Update `CHANGELOG.md` under **Unreleased** or new patch section.

## If hotfix cannot wait for tag

- Build image from commit SHA `sha-<short>`; deploy that immutable reference; tag later for bookkeeping.
