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
