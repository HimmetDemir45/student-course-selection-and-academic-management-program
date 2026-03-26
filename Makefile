SHELL := /usr/bin/env bash
PYTHON ?= python
PYTEST ?= pytest
BANDIT_PYTHON ?= $(PYTHON)

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
	$(BANDIT_PYTHON) -m bandit -r . -x "./tests,./.venv,./venv" --severity-level medium --confidence-level medium
	test -f .secrets.baseline
	python -m detect_secrets scan --baseline .secrets.baseline --all-files \
		--exclude-files '(htmlcov/|\.coverage$$|coverage\.xml|node_modules/|\.git/|__pycache__/|\.pyc$$|\.idea/|agent-transcripts/|mcps/)'
	python -m detect_secrets audit .secrets.baseline --stats

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
