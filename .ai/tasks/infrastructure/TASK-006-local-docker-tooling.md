# Task

## ID
TASK-006

## Title
Local Docker environment (optional developer tooling) — DEFERRED

## Feature
FEAT-001 — Backend Platform Foundation

## Description
**Re-scoped 2026-09-27 (ADR-015, ADR-016, ADR-018): deferred to the backlog.** The PO decided that the server is the reference runtime, there is no Docker on the server, and test suites run on the server (REQ-009). A local Docker environment is optional convenience tooling and is not an acceptance gate for FEAT-001.

When picked up again, it provides under the ADR-012 layout: the backend Dockerfile (`python:3.13-slim`, non-root, gunicorn) and entrypoint, `deploy/docker/compose/local.yml`, and local-only root Makefile targets (`up`, `down`, `logs`). The root `Makefile` and root `.env.example` are now created by **TASK-012/TASK-013**; this task would only add local targets to them.

## Business Requirement
REQ-002; DRF_SKILL.md §41–42, §52, §57; ADR-009, ADR-012; FEAT-001 criterion 1

## Agent
Infrastructure

## Scope (allowed paths)
- `deploy/docker/backend/**`, `deploy/docker/compose/local.yml`
- root `Makefile` (local targets only: `up`, `down`, `logs`, `ps`, `backend-shell`, `backend-test`)
- root `.env.example` (local and deployment basics: `APP_NAME`, `APP_ENV`, `DEPLOYMENT_MODE`, `BACKEND_PORT`, `DOCKER_COMPOSE_FILE`, `BACKEND_SERVICE`, `HEALTH_CHECK_PASSWORD`)
- `deploy/README.md` (the "Local development" section only)

## Dependencies
- TASK-013 (root Makefile/.env.example exist), TASK-003 (migrate needs the custom user model)
- A PO/PM decision to schedule it (not in sprint-01)

## Acceptance Criteria

- [ ] `deploy/docker/backend/Dockerfile`: `python:3.13-slim`, multi-stage, non-root user, production-capable (gunicorn), and `requirements/development.txt` only in the dev target.
- [ ] `deploy/docker/backend/entrypoint.sh` + `wait_for_db.sh`: wait for the DB when `DATABASE_URL` is Postgres, run migrations only when `RUN_MIGRATIONS=true` (local default), then exec the command. `set -euo pipefail`.
- [ ] `docker compose -f deploy/docker/compose/local.yml config` validates. The backend is reachable on `${BACKEND_PORT}`. Redis and Postgres sit behind compose profiles (`redis`, `postgres`) and are not started by default.
- [ ] The container healthcheck calls `/api/health/` with the `X-Health-Check-Token` header from the env, without printing it.
- [ ] `make up` / `make down` / `make backend-test` work. `make backend-test` runs pytest inside the container on Python 3.13.
- [ ] No secrets in the Dockerfile, compose file or Makefile. `.env` is git-ignored.
- [ ] `deploy/README.md` documents the local workflow.

## Technical Notes

- Scope unchanged if resumed, except: no container tests are QA evidence (ADR-018), and no Docker on the server (ADR-015).
- `backend/Makefile` belongs to Backend (TASK-001).

## Testing Requirements

- `docker compose … config`, image build, `make up`, the health check green, and `make backend-test` passing. Record the commands and their output in the Completion Report.
- `bash -n` / `shellcheck` on the scripts.

## Plan Review Required
Yes — Docker architecture (when resumed)

## Status

BACKLOG

## Activity Log
- 2026-09-27 | team-lead | — → TODO | created from sprint-01 technical plan (as Backend task)
- 2026-09-27 | team-lead | TODO → TODO | reassigned Backend → Infrastructure, scope moved to `deploy/` (ADR-012)
- 2026-09-27 | team-lead | TODO → BACKLOG | PO: server is the reference runtime, no Docker on server, tests on server (ADR-015/016/018); local Docker optional; root Makefile/.env.example moved to TASK-012/013

## Implementation Plan
(assignee: required before coding — wait for TL APPROVED)

## Completion Report
(assignee, when moving to READY_FOR_REVIEW)
- Files changed:
- Tests added:
- Validation commands run + results:
- Contract/OpenAPI changes:
- Known limitations / remaining problems:

## Review Log

## QA Log

## Sign-off
- TL final review: ☐
- QA verdict: ☐
- PM acceptance: ☐
