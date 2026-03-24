# AGENTS.md

## Project snapshot
- Stack: **Django 5 (Python 3.12+)** + server-rendered Django Templates, with MySQL as the primary database.
- Architecture target: Django’s MVT structure organized to satisfy course-required **MVC separation** (clear separation between model/business logic/view/controller responsibilities).
- This repository is in migration from an initial Flask scaffold to Django. Flask-specific runtime/contracts are deprecated and should not be extended.
- Project domain: **Öğrenci Ders Seçim ve Akademik Yönetim Sistemi** (student course registration and academic management platform).

## Primary goals and constraints (course-aligned)
- Implement a modern web application with strict layered architecture.
- Apply secure authentication/session management.
- Implement complete CRUD workflows.
- Enforce role-based authorization (e.g., admin / student / instructor).
- Apply security controls (SQLi/XSS/CSRF/brute-force/error hardening).
- Maintain relational schema with **at least 12 related tables**.
- Keep development traceable via regular GitHub commits and weekly progress checkpoints.
- Prepare for cloud deployment (target: AWS Free Tier-compatible).

## Django architecture and request flow
- Project-level config package: `config/`
  - `config/settings/base.py`
  - `config/settings/dev.py` (local development; default in `manage.py`)
  - `config/settings/prod.py` (production: RDS `DATABASE_URL`, S3, security headers)
  - `config/settings/ci.py` (GitHub Actions + MySQL service)
  - `config/settings/development.py` / `production.py` — backward-compatible aliases for `dev` / `prod`
- URL entry:
  - `config/urls.py` includes app-level route modules.
- App structure (planned baseline):
  - `accounts`
  - `core`
  - `students`
  - `instructors`
  - `courses`
  - `enrollments`
  - `academic`
  - `dashboard`
  - `audit_logs`
- Request flow (target):
  - HTTP request -> `config/urls.py` -> `app/urls.py` -> `views.py` (or class-based views) -> service/domain layer (if applicable) -> model/repository -> template response.
- Error flow:
  - Centralized custom handlers in project-level URL config and shared error templates (`templates/errors/404.html`, `templates/errors/500.html`).

## Environment and configuration contracts
- Environment variables are loaded from `.env` (via `django-environ` or equivalent).
- Expected variables (see `.env.example` and `.env.production.example`):
  - `DJANGO_SETTINGS_MODULE` (e.g. `config.settings.dev` / `config.settings.prod`)
  - `DJANGO_SECRET_KEY` (or legacy `SECRET_KEY` in dev)
  - `DJANGO_DEBUG` / `DEBUG` (dev)
  - `DJANGO_ALLOWED_HOSTS`
  - `DJANGO_CSRF_TRUSTED_ORIGINS` (production HTTPS)
  - `DATABASE_URL` (Docker / RDS) **or** `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`
  - `AWS_*` for S3 static/media in production (`django-storages`)
  - `LOG_LEVEL` (optional)
- Default database engine: MySQL.
- Security defaults to preserve:
  - CSRF protection enabled.
  - Secure password hashing via Django auth hashers.
  - No sensitive stack traces exposed in production.

## Developer workflows
- Install dependencies:
  - `pip install -r requirements.txt`
- Apply migrations:
  - `python manage.py makemigrations`
  - `python manage.py migrate`
- Run local server:
  - `python manage.py runserver`
- Create admin user:
  - `python manage.py createsuperuser`
- Run tests:
  - `python manage.py test`
- Lint / coverage / dependency audit (optional dev bundle: `pip install -r requirements-dev.txt`):
  - `python -m ruff check .`
  - `coverage run manage.py test` then `coverage report` (fail threshold in `pyproject.toml`)
  - `python -m pip_audit -r requirements.txt --strict`
- Load Phase 4 seed fixture (optional):
  - `python manage.py loaddata phase4_seed` (fixture path: `core/fixtures/phase4_seed.json`; dev password for seed users: `seedpass123`)

> If new workflows are introduced (lint, formatting, CI commands, container flow), append exact runnable commands to this file.

## Project-specific coding patterns
- Keep view layer thin; avoid embedding business rules directly in templates/views.
- Place reusable domain logic in service-oriented modules where appropriate (e.g., `services.py` per app or `core/services/`).
- Keep ORM logic in `models.py` (or clearly structured model modules).
- Register app routes only through each app’s `urls.py` and include them in `config/urls.py`.
- Templates must inherit from a shared base layout (`templates/base.html`).
- Use Django messages framework for user-facing operation feedback (success/error/info).
- Keep admin-specific actions scoped under `dashboard` and permission-protected views.

## Security implementation rules
- Use Django ORM/prepared operations to prevent SQL injection.
- Keep CSRF protection active for all state-changing requests.
- Validate and sanitize user input through Django Forms/ModelForms/serializers as applicable.
- Escape output in templates (default auto-escape must remain enabled).
- Enforce authentication + authorization checks on protected endpoints.
- Implement brute-force mitigation strategy for login endpoints (rate limiting / lockout policy).
- Do not leak system internals in end-user error responses.

## Authorization and identity rules
- Use Django authentication system as the foundation.
- Implement role-based access control for at least:
  - `admin`
  - `student`
  - `instructor`
- Reserve/implement flows for:
  - registration
  - login/logout
  - remember-me behavior
  - password reset
  - session timeout handling
- All protected management routes must be inaccessible to unauthorized users.

## Database and schema rules
- Minimum **12 related tables** is mandatory.
- Define explicit foreign-key relationships and constraints.
- Every core entity must support full CRUD where relevant.
- Maintain migration history consistently via Django migrations.
- Avoid raw SQL unless absolutely necessary; if used, parameterize safely and document why.

## Integration points to preserve
- Shared utilities and cross-cutting concerns should live in `core`.
- Operational/audit events should flow into `audit_logs`.
- Academic lifecycle logic (term, grading, transcript-related structures) should remain under `academic`.
- Course registration/enrollment lifecycle should be centered in `enrollments` with clear boundaries from `courses` and `students`.

## Migration note (Flask -> Django)
- Do **not** add new Flask blueprints/routes/extensions.
- Do **not** rely on Flask app factory/runtime environment mapping anymore.
- Flask-era files may remain temporarily for reference, but new implementation must be Django-native.
- During transition, prioritize feature parity by module (accounts -> courses -> enrollments -> academic -> dashboard).

## Agent checklist before submitting changes
- Confirm changes respect layered separation (no business logic in templates).
- Confirm new URLs are registered in correct app and included at project level.
- Confirm permission checks exist on protected views.
- Confirm CSRF/auth/session behavior remains valid after changes.
- Confirm migrations are generated for schema updates.
- Confirm README and this AGENTS.md are updated when commands/processes change.
- Confirm code aligns with the current phase plan (scaffold first, then auth, then domain modules, then hardening/deployment).

## Delivery-phase documentation expectations
- Keep `README` updated with setup/run/deploy instructions.
- Maintain `migration_notes.md` for Flask-to-Django mapping decisions.
- Ensure contribution traceability via small, regular commits (not one-shot bulk upload).