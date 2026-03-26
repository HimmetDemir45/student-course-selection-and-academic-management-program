SHELL := /usr/bin/env bash
PYTHON ?= python
PYTEST ?= pytest

export PYTHONUNBUFFERED=1
export DJANGO_SETTINGS_MODULE ?= config.settings.dev

.PHONY: test test-unit test-integration test-smoke test-concurrency security-scan migration-smoke canary ci

test:
	$(PYTEST) -m "unit or integration or smoke or concurrency or security"

test-unit:
	$(PYTEST) -m "unit"

test-integration:
	$(PYTEST) -m "integration"

test-smoke:
	$(PYTEST) -m "smoke"

test-concurrency:
	$(PYTEST) -m "concurrency"

security-scan:
	python -m pip_audit -r requirements.txt --strict
	bandit -c .bandit -r . -x "./tests,./.venv,./venv" -ll
	test -f .secrets.baseline
	detect-secrets scan --baseline .secrets.baseline --all-files
	detect-secrets audit .secrets.baseline --stats

migration-smoke:
	chmod +x scripts/smoke_migration.sh
	./scripts/smoke_migration.sh

canary:
	chmod +x scripts/synthetic_canary.sh
	./scripts/synthetic_canary.sh

ci: security-scan migration-smoke
	$(PYTEST) -m "unit"
	$(PYTEST) -m "integration"
	$(PYTEST) -m "smoke"
	$(PYTEST) --cov=. --cov-report=xml:coverage.xml --cov-report=term-missing --cov-fail-under=80 -m "unit or integration or smoke or concurrency or security"
