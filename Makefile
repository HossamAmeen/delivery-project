# Flash — operations Makefile (Infrastructure-owned, ADR-012). Developer targets live in backend/Makefile.
# Every target reads the root .env (copy .env.example → .env) and delegates to deploy/scripts/*.
# DRY_RUN=1 prints the steps without changing anything. Only DEPLOYMENT_MODE=systemd is implemented.
#
# Tests and QA never run locally (REQ-009, ADR-018): they run on the server through these targets.

SHELL := /bin/bash
.DEFAULT_GOAL := help
SCRIPTS := deploy/scripts
yes = $(filter 1 true yes,$(1))
DRY := $(if $(call yes,$(DRY_RUN)),--dry-run,)
TARGET ?= all
LINES ?= 200

.PHONY: help setup-server deploy restart migrate collectstatic health rollback tls prune seed-qa-users \
        logs status render test-backend-remote qa-remote throttle-reset

help: ## List the targets
	@echo "Flash ops targets (DRY_RUN=1 prints the steps without executing them):"
	@grep -E '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*## "}{printf "  make %-22s %s\n", $$1, $$2}'
	@echo
	@echo "Examples:"
	@echo "  make setup-server DRY_RUN=1          make setup-server BOOTSTRAP_ONLY=1      make setup-server WITH_E2E=1"
	@echo "  make deploy                          make deploy ALLOW_DIRTY=1               make health"
	@echo "  make restart TARGET=backend          make rollback                           make rollback TO=<id> RESTORE_DB=never"
	@echo "  make logs LINES=500 FOLLOW=1         make status                             make tls"
	@echo "  make test-backend-remote WORKTREE=1  make test-backend-remote REF=<commit>   make qa-remote ARGS='-m smoke'"

setup-server: ## Server setup: layout+modes, uv, Python, shared/.env, unit, nginx [BOOTSTRAP_ONLY=1] [WITH_E2E=1]
	@$(SCRIPTS)/setup-server.sh $(DRY) $(if $(call yes,$(BOOTSTRAP_ONLY)),--bootstrap-only,) $(if $(call yes,$(WITH_E2E)),--with-e2e,)

deploy: ## Build locally + deploy a new release (health-checked, auto-rollback) [ALLOW_DIRTY=1]
	@$(SCRIPTS)/deploy.sh $(DRY) $(if $(call yes,$(ALLOW_DIRTY)),--allow-dirty,)

restart: ## Restart [TARGET=backend|frontend|all] (default all)
	@$(SCRIPTS)/restart.sh $(TARGET) $(DRY)

migrate: ## SQLite backup + migrate for the current release (prints the plan first)
	@$(SCRIPTS)/migrate.sh $(DRY)

collectstatic: ## collectstatic for the current release
	@$(SCRIPTS)/collectstatic.sh $(DRY)

health: ## Health check (local + public HTTPS + web + unit + nginx -t) [TIMEOUT=<s>]
	@$(SCRIPTS)/health-check.sh $(DRY) $(if $(TIMEOUT),--timeout $(TIMEOUT),)

rollback: ## Roll back to the previous release [TO=<id>] [RESTORE_DB=auto|always|never]
	@$(SCRIPTS)/rollback.sh $(DRY) $(if $(TO),--to $(TO),) $(if $(RESTORE_DB),--restore-mode $(RESTORE_DB),)

tls: ## Issue the Let's Encrypt cert for the two Flash names + switch nginx to TLS (idempotent)
	@$(SCRIPTS)/tls.sh $(DRY)

prune: ## Apply retention (RELEASES_TO_KEEP, DB_BACKUPS_TO_KEEP)
	@$(SCRIPTS)/prune.sh $(DRY)

seed-qa-users: ## Create/update the QA users; passwords → /srv/flash/qa/credentials.env (server only)
	@$(SCRIPTS)/seed-qa-users.sh $(DRY)

render: ## Render all templates locally (inspection only) [OUT=<dir>]
	@$(SCRIPTS)/render-templates.sh $(if $(OUT),--out $(OUT),)

logs: ## Journald logs of the Flash unit [LINES=200] [FOLLOW=1]
	@$(SCRIPTS)/status.sh logs $(LINES) $(if $(call yes,$(FOLLOW)),--follow,)

status: ## Unit state, current release, releases, disk, certificate, Flash nginx files
	@$(SCRIPTS)/status.sh status

test-backend-remote: ## Backend lint/check/migrations/pytest on the server [REF=<ref>|WORKTREE=1] [STEPS=] [ARGS=]
	@$(SCRIPTS)/remote-test.sh $(DRY) backend \
	  $(if $(call yes,$(WORKTREE)),--worktree,$(if $(REF),--ref $(REF),)) \
	  $(if $(STEPS),--steps $(STEPS),) -- $(ARGS)

qa-remote: ## QA pytest suite on the server against the public HTTPS URLs [ARGS="-m smoke"]
	@$(SCRIPTS)/remote-test.sh $(DRY) qa -- $(ARGS)

throttle-reset: ## Empty the server throttle cache (shared/cache) and print the removed count
	@$(SCRIPTS)/remote-test.sh $(DRY) throttle-reset
