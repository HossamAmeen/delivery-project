# Developer targets (DRF_SKILL §45). Deployment/ops targets live in the repo-root
# Makefile (Infrastructure, ADR-012); the ones below delegate to it.
# Test suites run on the server (REQ-009, ADR-018): use `make test-remote`.

PYTHON ?= python
MANAGE := $(PYTHON) manage.py

.PHONY: install install-dev run migrate makemigrations makemigrations-check test coverage \
	test-rate-limit check check-deploy lint format format-check shell collectstatic schema \
	celery-worker celery-beat test-remote docker-local docker-staging docker-production \
	deploy deploy-staging deploy-production

install:
	$(PYTHON) -m pip install -r requirements/production.txt

install-dev:
	$(PYTHON) -m pip install -r requirements/development.txt

run:
	$(MANAGE) runserver

migrate:
	$(MANAGE) migrate

makemigrations:
	$(MANAGE) makemigrations

makemigrations-check:
	$(MANAGE) makemigrations --check --dry-run

test:
	$(PYTHON) -m pytest

coverage:
	$(PYTHON) -m pytest --cov=. --cov-report=term-missing

test-rate-limit:
	$(PYTHON) -m pytest -k "throttle or rate_limit"

check:
	$(MANAGE) check

check-deploy:
	DJANGO_SETTINGS_MODULE=config.settings.production $(MANAGE) check --deploy

lint:
	ruff check .

format:
	ruff format .

format-check:
	ruff format --check .

shell:
	$(MANAGE) shell

collectstatic:
	$(MANAGE) collectstatic --noinput

schema:
	$(MANAGE) spectacular --validate --fail-on-warn --file schema.yml

celery-worker:
	celery -A config worker --loglevel=INFO

celery-beat:
	celery -A config beat --loglevel=INFO

# --- Delegated to the repo-root Makefile (ADR-012, ADR-018) ---
test-remote:
	$(MAKE) -C .. test-backend-remote WORKTREE=1

docker-local docker-staging docker-production:
	$(MAKE) -C .. $@

deploy deploy-staging deploy-production:
	$(MAKE) -C .. deploy
