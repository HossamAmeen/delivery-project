---
name: infra-change
description: Flash Infrastructure procedure for changing deploy tooling (deploy/ scripts, nginx/systemd templates, env templates, root Makefile, CI) — inspect first, design for TL plan review, follow the mode/no-hardcoding/secrets/release-layout rules, validate with shellcheck, render, DRY_RUN in place, document in deploy/README.md, and write a validation report.
---

# Infrastructure — change deploy tooling

Authority: `.ai/agents/infrastructure.md`, `deploy/README.md`, and ADR-012/013/014/015/016/017/018. Current reality: systemd mode only, shared VPS `hossam@34.123.215.195`, SQLite, no Docker or Redis on the server, backend on `127.0.0.1:8010`. **Never touch the dental-clinic app**, its nginx sites or its units.

## 1. Inspect before you build (never design for an architecture you have not looked at)
- `backend/manage.py`, `backend/config/wsgi.py`, `backend/requirements/`, `backend/.env.example`
- `frontend/package.json` and the `dist/` output
- the existing `deploy/`, `Makefile`, `.env.example`, `.github/`
- `api-contracts.md` § Foundation for the real health endpoints: `/api/health/` and `/api/health/ready/` with `X-Health-Check-Token`, and `/api/status/`. **Never invent a health check.**

## 2. Design → `.ai/reports/infrastructure/<FEAT|TASK>-infra-design.md`
Cover what changes, why, the effect on the server and on dental, the rollback path, and the secrets handling. The TL approves it as the plan review before you implement.

## 3. Rules every change follows
- `DEPLOYMENT_MODE` is read from `.env` by every script. An invalid or missing value exits non-zero with a clear message.
- Single entry points: `deploy.sh`, `restart.sh <backend|frontend|all>`, `migrate.sh`, `health-check.sh`, `rollback.sh`, `setup-server.sh`. Shared helpers go in `deploy/scripts/lib/common.sh`.
- **Nothing hardcoded.** Domains, ports, paths, users, hosts and service names come from `.env`. nginx and systemd files are `*.template`, rendered with `envsubst` **and an explicit variable list** (so nginx's `$host`/`$uri` survive).
- **Secrets:**
  - never in templates, scripts, workflows or logs
  - `set -euo pipefail`; never `set -x` near a secret; redact values in logs
  - SSH keys are referenced by `SSH_KEY_PATH`, never echoed
  - passwords go through stdin or env, never argv
- Release layout: `${DEPLOY_PATH}/{current -> releases/<UTC ts>, releases/, shared/{.env,db,media,logs,cache,backups}}`. Keep `RELEASES_TO_KEEP`.
- Migrations:
  - run once per deploy, before traffic, with a SQLite backup first (ADR-017)
  - rollback restores that backup; it never reverse-migrates
  - flag any migration that is not backward-compatible
- Every nginx change uses **safe-apply**: back up → write → `nginx -t` → restore on failure, never reload a failing config, never restart nginx, never use `default_server`.
- Every script supports `--dry-run` (`make <target> DRY_RUN=1`), which prints the steps and redacts secrets.
- Never edit application code (`backend/apps|config|common`, `frontend/src`). An app-side need becomes a blocker for the TL.
- Never weaken a CI gate.

## 4. Validate (record every command and its result)
```bash
(cd deploy/scripts && bash -n *.sh lib/*.sh && shellcheck -x -P . *.sh lib/*.sh)
make render OUT=<scratchpad>/render          # inspect; check that no ${VAR} is left unrendered
make <changed target> DRY_RUN=1              # every changed entry point
make status && make health                   # read-only, against the server
```
- Validate the rendered nginx config with `nginx -t` (on the server it runs inside safe-apply/health), and rendered units with `systemd-analyze verify` where available.
- CI (BLK-012): no remote yet, so lint the workflows only (for example `actionlint`) and report "pipeline not run".
- **Never claim you tested in the target environment without evidence.**

## 5. Finish
- Update `deploy/README.md`, including the operator runbook for any live step.
- Write `.ai/reports/infrastructure/TASK-NNN-validation-YYYY-MM-DD.md`.
- Fill in the Completion Report, set `READY_FOR_REVIEW`, and add an Activity Log line.
