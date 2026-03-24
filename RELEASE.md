# Release process (SemVer)

## Versioning

- **MAJOR** (X.0.0): incompatible API/behavior changes for operators or documented contracts.
- **MINOR** (x.Y.0): backward-compatible features.
- **PATCH** (x.y.Z): backward-compatible fixes (security patches bump PATCH).

Pre-releases: `v1.0.0-rc.1`, `v1.0.0-beta.2` (tag as-is; CI/release workflow accepts any `v*` tag).

## Release candidate (RC) flow

1. Branch from `main` (or `develop` if you use it): `release/1.0.0` or work on `main` with feature freeze.
2. Open PR; CI must be green (lint, security, test + coverage).
3. Tag RC when QA agrees: `git tag v1.0.0-rc.1 && git push origin v1.0.0-rc.1`
   - **Release** workflow builds and pushes `ghcr.io/<owner>/<repo>` with semver + sha tags.
4. Deploy RC to **staging**; run UAT (`docs/go-live-checklist.md`).
5. After sign-off, tag **final**: `git tag v1.0.0 && git push origin v1.0.0`
6. Update `CHANGELOG.md` (move Unreleased → dated section), commit on `main`, or amend policy to commit changelog before tag (team choice).
7. Deploy **prod** per `docs/runbooks/deployment-runbook.md`.
8. Run post-release checks: `docs/post-release-verification.md` and optional `smoke-tests` workflow.

## Git tag → prod (short)

1. `git tag vX.Y.Z && git push origin vX.Y.Z`
2. GitHub **Release** workflow: CI → Docker build → GHCR (`vX.Y.Z`, `sha-…`)
3. On server: pull immutable tag, `migrate`, restart app (see deployment runbook).
4. If `HEALTHCHECK_BASE_URL` secret is set, workflow runs `/health/live` + `/health/ready`.
5. Otherwise run **Smoke tests** manually (Actions → Smoke tests) with production base URL.

## Rollback pointer

Failure path output is summarized in the Release workflow job **rollback-hint**. Full steps: `docs/runbooks/rollback-runbook.md`.

## Artifacts

- Container: `ghcr.io/<github_repository>:<semver>` and `:sha-<short>`
- Source: Git tag and GitHub Releases page (optional release notes paste from CHANGELOG).
