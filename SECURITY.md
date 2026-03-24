# Security policy

## Supported versions

| Track   | Supported                                      |
|---------|------------------------------------------------|
| `main`  | Latest commit; Django/MySQL stack per `README` |
| Tags    | Release tags only if your fork creates them    |

Out-of-support dependencies should be upgraded; `pip-audit` (see `README`) is the source of truth for known CVEs pinned in `requirements.txt`.

## Reporting a vulnerability

Please **do not** open a public GitHub issue for undisclosed security problems.

1. Email or contact the repository maintainers through a **private** channel (course instructor, organization security contact, or GitHub private security advisory if enabled).
2. Include: affected component (URL or module), reproduction steps, impact, and any suggested fix.
3. Allow a reasonable disclosure window before public discussion.

Maintainers will acknowledge receipt, assess severity, and coordinate a patch release or advisory.

## Secret leak incident response (mini runbook)

1. **Contain**: Rotate the exposed credential immediately (see “Key rotation” below). Assume the secret is compromised.
2. **Repos**: Remove files from the Git index (not only `.gitignore`): `git rm --cached <path>` then commit; consider `git filter-repo` / BFG if history contains secrets (GitHub Support may help for public leaks).
3. **GitHub**: Revoke any exposed tokens; enable **push protection** and **secret scanning**; review Dependabot alerts.
4. **Application**: Invalidate sessions if `DJANGO_SECRET_KEY` leaked; force password reset for affected users if DB passwords or user secrets leaked.
5. **Document**: Post-incident note (internal): root cause, timeline, and preventive actions (pre-commit hooks, review checklist).

## Key rotation (placeholders only — use your real values in secrets stores)

### `DJANGO_SECRET_KEY`

1. Generate a new secret (long random string).
2. Set the new value in the environment / secrets manager (e.g. AWS Secrets Manager, `.env.production` **not** committed).
3. Redeploy all app instances with the new value.
4. **All users are logged out** when the key changes (sessions invalidated).

### Database password (`DATABASE_URL` or `DB_PASSWORD`)

1. Change password in MySQL/RDS for the application user.
2. Update `DATABASE_URL` / `DB_*` in the deployment environment.
3. Restart workers; verify `/health/ready/`.

### AWS keys (`AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`)

1. Create a new IAM access key (or migrate to IAM role / instance profile and remove long-lived keys).
2. Update environment variables or instance profile.
3. Disable and delete the old key after validation.

### SMTP or third-party API tokens

1. Revoke the token in the provider dashboard.
2. Issue a new token; update environment only on the server/CI secrets store.

## Design notes (Phase 6)

- Production settings enforce TLS redirects, HSTS, secure cookies, CSRF trusted origins, and `DEBUG=False` (see `config/settings/prod.py`).
- Logs use a redacting formatter for common credential patterns (`core/logging_utils.py`); never log raw secrets in application code.
- CI runs `pip-audit --strict` on `requirements.txt` to fail builds on known vulnerable pinned versions.

## Incident escalation (Phase 7)

| Stage | Who | When |
|-------|-----|------|
| L1 | On-call engineer / maintainer | First response, triage per `docs/runbooks/incident-response.md` |
| L2 | Tech lead / repo admin | SEV1 or no progress in 15–30 min |
| L3 | Organization / instructor / AWS support | Data breach, regional outage, legal/compliance |

Escalation contacts are **not** listed in this file; keep them in a private ops wiki or team roster.

## Credential rotation cadence (recommended)

| Secret | Suggested cadence | Notes |
|--------|-------------------|--------|
| `DJANGO_SECRET_KEY` | Only on compromise or annual drill | Invalidates all sessions |
| DB password | 90–180 days or on staff change | Update `DATABASE_URL`, rolling restart |
| AWS IAM access keys | Prefer roles; if keys, ≤ 90 days | Prefer instance profile / OIDC |
| GitHub PAT / deploy tokens | Per org policy; revoke when people leave | Use fine-scoped tokens |

Document actual dates in your internal tracker.

## Access review (quarterly checklist)

- [ ] GitHub **collaborators** and **teams**: least privilege; remove alumni accounts.
- [ ] **Branch protection** on `main`: required checks, no direct push, reviews enforced (`README` Phase 7).
- [ ] **AWS IAM**: no unused users/keys; MFA on human users; app uses role not long-lived keys where possible.
- [ ] **RDS**: security groups only from app tier; no public `0.0.0.0/0` on 3306.
- [ ] **Secrets**: not in repo history; scanning + push protection enabled.

## GitHub branch protection (target state)

- `main`: require pull request before merge; required status checks (**lint**, **security**, **test** from CI); require approvals ≥ 1; dismiss stale approvals; **include administrators** optional per org; block force pushes; block deletions.
- Optional: **Require CODEOWNERS review** for paths in `CODEOWNERS`.

## Request correlation

- HTTP responses include **`X-Request-ID`** (see `core/middleware/request_id.py`). Support staff can collect this from browser devtools or proxy logs to correlate with application and ALB logs.
