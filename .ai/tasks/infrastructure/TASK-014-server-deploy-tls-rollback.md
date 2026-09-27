# Task

## ID
TASK-014

## Title
Server setup, first deployment, TLS, QA seeding and rollback exercise on the shared VPS

## Feature
FEAT-004 — Deployment & Environments (also delivers the deployed instance FEAT-001 and FEAT-003 are verified on)

## Description
Use the reviewed TASK-013 tooling to bring Flash live on `34.123.215.195`:
`make setup-server` → first `make deploy` (HTTP bootstrap) → `make tls` → full HTTPS config → `make health` → `make seed-qa-users` → `setup-server --with-e2e` → rollback exercise → roll forward → crash-restart check. Every step with dental-clinic guard evidence. Produce the deployment report.

## Business Requirement
REQ-008, REQ-009; BLK-011; ADR-013, ADR-015, ADR-016, ADR-017, ADR-018; FEAT-004 criteria 2–11 (execution evidence), FEAT-003 AC6, FEAT-001 AC1/AC10

## Agent
Infrastructure

## Scope (allowed paths)
- Execution only: root `.env` (operator values, git-ignored; `LETSENCRYPT_EMAIL` optional), `.ai/reports/infrastructure/**`
- Server: exactly what TASK-013's constraints allow (`/srv/flash/**`, the Flash unit, the two Flash nginx site files, the `flash-delivery` certificate, Playwright deps with `--with-e2e`)
- Fixes to `deploy/**`/`Makefile` found during execution are allowed but must be listed in the Completion Report and go through TL review with this task

## Dependencies
- TASK-013 **READY_FOR_QA** (TL-reviewed tooling)
- TASK-001, TASK-002, TASK-005, TASK-004, TASK-003 **READY_FOR_QA** (deployable backend with the custom user model, health, status, `create_role_user`)
- TASK-007 **READY_FOR_QA** (deployable PWA)
- `LETSENCRYPT_EMAIL` is **optional** (amended 2026-09-27, ADR-015 § TLS): leave it empty to reuse the server's registered Let's Encrypt production account; fill it only if the operator supplies one (never invent one)

## Acceptance Criteria
- [ ] `make setup-server` on the server: unit installed + enabled, `shared/.env` created with generated secrets (0600, owner hossam), nginx bootstrap sites applied via safe-apply; dental guard identical before/after. Directory modes per ADR-015 § Layout "Permissions" (`stat` evidence: `shared` 0751, `db`/`backups`/`cache` 0700, `static`/`media` 0755).
- [ ] First `make deploy` from a clean commit on `main`: release created, venv on Python 3.13, DB created by `migrate`, `current` switched, `flash-backend` active on `127.0.0.1:8010` only (`ss -ltn` evidence: not on 0.0.0.0), HTTP health green.
- [ ] `make tls`: one certificate `flash-delivery` covering exactly `api.delivery.hossam-ameen.online` and `delivery.hossam-ameen.online` (`sudo certbot certificates` excerpt); full HTTPS templates applied; `http://` → 301 `https://` on both; `certbot renew --dry-run --cert-name flash-delivery` succeeds; dental sites and their certificates unchanged.
- [ ] `make health` green: `/api/health/` + `/api/health/ready/` (127.0.0.1 and HTTPS, header token, `celery: skipped`), `https://delivery.hossam-ameen.online/` 200, deep link `/driver` 200 (SPA), `https://api.delivery.hossam-ameen.online/api/status/` 200, and a collected static file (e.g. an admin/Jazzmin CSS under `/static/`) served **200, not 403**, through `https://api.delivery.hossam-ameen.online/static/…` (proves `www-data` can traverse `shared/`) — with no token in any output or log (`grep` of the deploy log, `/var/log/nginx/flash-api.access.log` **and `journalctl -u flash-backend`** for the token value done **on the server** and reported as a count only). Also send one `GET /api/health/?password=<a wrong dummy value>` and show that neither the nginx access log nor the gunicorn access log in journald contains the query string (count only).
- [ ] `make seed-qa-users` done (incl. `qa_inactive`, inactive, once TASK-016 is merged — otherwise report it as skipped); `/srv/flash/qa/credentials.env` 0600; usernames listed; `setup-server.sh --with-e2e` done with disk before/after.
- [ ] **Rollback exercise:** deploy a second release (a new commit, or the same commit with `--allow-same-sha` if the tooling provides it), then `make rollback` → previous release active, health green, DB restore behaviour as ADR-017 (report whether a restore happened and why), then `make deploy` again so the final state is the latest commit, health green.
- [ ] Crash recovery: `sudo systemctl kill -s KILL flash-backend` → service back to active within ~10 s and health green; `systemctl is-enabled flash-backend` = enabled (**do not reboot** the shared server).
- [ ] Resource evidence: `free -m`, `df -h /srv`, `systemctl show flash-backend -p MemoryCurrent,MemoryMax`, release and backup counts after pruning.
- [ ] Dental non-interference evidence for **every** step (guard output) + a final dental check (`systemctl is-active dental-clinic-backend`, both dental URLs' status codes).
- [ ] `.ai/reports/infrastructure/FEAT-004-deployment-report.md`: every command run, redacted output excerpts, timings, the release ids/SHAs, final state, anything that deviated. Completion Report links it. `make throttle-reset` done at the end.

## Technical Notes — pre-approved constraints (TL, 2026-09-27)
- Same constraints as TASK-013 (sudo list now includes `systemctl stop|start ${BACKEND_SYSTEMD_SERVICE}` for the rollback DB restore — Flash unit only; full list in ADR-015 "sudo on the server").
- **From the TASK-013 review (2026-09-27), before the first live apply:**
  - **BLK-013 RESOLVED → `NGINX_HTTP2=off`, mandatory.** Keep it off in `.env`; first make `lib/templates.sh` refuse `on` (exit 2). Evidence: installed Flash files have no `http2`, and `sudo nginx -t` after each apply shows **no** `protocol options redefined` warning; `curl -sI --http2 https://dental.hossam-ameen.online/` negotiates the same protocol before and after (report both).
  - Extend the `deploy.sh` dirty-tree check to `deploy/` and the root `Makefile` (recorded in `REVISION`). These two fixes go into the Completion Report and through TL review with this task.
  - Commits: `make deploy` refuses until `backend/` and `frontend/` are committed — ask the orchestrator; do not use `--allow-dirty` for the deploy that becomes the release of record.
  - Health before `make tls` runs over http with the token endpoints on 127.0.0.1 only (accepted); after `make tls`, `make health` must pass the https token checks.
  - collectstatic's duplicate `admin/js/popup_response.js` warning is expected (jazzmin), not a failure. If any guard reports a dental difference: stop, do not continue, restore the Flash change that preceded it, and report to the TL immediately (set BLOCKED with a blocker file).
- If `nginx -t` fails at any point, safe-apply restores; never force a reload.
- If certbot fails (DNS, rate limit), stay on the HTTP bootstrap (site still up over HTTP) and report; do not retry more than twice (Let's Encrypt rate limits).
- Never print or copy `shared/.env` or `credentials.env` content to the local machine or into reports.

## Testing Requirements
- The executed steps above are the test. QA verifies independently in TASK-015/009/010.

## Plan Review Required
Yes — production deployment on a shared server. **Pre-approved** by the TL on 2026-09-27 against the TASK-013 constraints and this task's criteria: write a ≤ 15-line `## Implementation Plan` (the step order above + stop conditions) and proceed once the dependencies are met. The TL reviews the execution evidence.

## Status

IN_PROGRESS

## Activity Log
- 2026-09-27 | team-lead | — → TODO | created for FEAT-004; starts after TASK-013 + backend chain + TASK-007 reach READY_FOR_QA; plan pre-approved
- 2026-09-27 | team-lead | TODO → TODO | amended from the TASK-012 review: permission evidence, `/static/` 200 check, `LETSENCRYPT_EMAIL` optional
- 2026-09-27 | team-lead | TODO → TODO | amended from the backend/QA reviews: journald token check + query-string log check, `qa_inactive` seeding
- 2026-09-27 | infrastructure | TODO → IN_PROGRESS | phase 1 (pre-live fixes, no live apply): NGINX_HTTP2=on refused (exit 2), dirty-tree check extended to deploy/ + Makefile (recorded in REVISION); waiting for the orchestrator's commit + go for the live phase
- 2026-09-27 | team-lead | IN_PROGRESS → IN_PROGRESS | phase 1 (pre-live fixes) reviewed and APPROVED; live phase may start after the orchestrator's commit

## Implementation Plan
Phase 1 (done, no live apply): `lib/templates.sh` refuses `NGINX_HTTP2=on` (exit 2, BLK-013); the `deploy.sh` dirty-tree check covers `backend/ frontend/ deploy/ Makefile` and records `dirty`, `dirty_paths` and `dirty_checked` in `REVISION`; the TASK-012 EXIT-trap fix is in `remote-test.sh`.
Phase 2 (live, after the orchestrator's commit + go). Every step is dental-guarded; STOP on any guard difference (restore the preceding Flash change, set BLOCKED + a blocker file, report to the TL):
1. Read-only baseline: `make status`, dental snapshot, `curl -sI --http2 https://dental.hossam-ameen.online/` protocol.
2. `make setup-server` → modes `stat` evidence, `shared/.env` (0600), unit installed + enabled, http bootstrap sites via safe-apply (`nginx -t` without `protocol options redefined`).
3. `make deploy` (clean commit, no `--allow-dirty`) → `ss -ltn` shows 127.0.0.1:8010 only, HTTP health green.
4. `make tls` (≤ 2 attempts; on failure stay on HTTP and report) → cert excerpt, 301s, renew dry-run, dental certificate unchanged.
5. `make health` (https token checks), `/driver` deep link, a `/static/` file 200, token/query-string log counts on the server.
6. `make seed-qa-users` (incl. `qa_inactive` if TASK-016 is merged), `make setup-server WITH_E2E=1` (disk before/after).
7. Rollback exercise: second release → `make rollback` → health → `make deploy` back to the latest; crash recovery via `systemctl kill -s KILL`.
8. Resource evidence, final dental check + dental http2 protocol comparison, `make throttle-reset`, `FEAT-004-deployment-report.md`.

## Completion Report
(assignee, when moving to READY_FOR_REVIEW)
- Files changed:
- Tests added:
- Validation commands run + results:
- Contract/OpenAPI changes:
- Known limitations / remaining problems:

## Review Log
- 2026-09-27 | team-lead | PLAN PRE-APPROVED (conditional) | valid within the TASK-013 constraints and ADR-015/017

### Review — 2026-09-27 — team-lead — code (phase 1: pre-live fixes)

**Verdict:** APPROVED (phase 1 only; the live execution evidence is reviewed when the task reaches READY_FOR_REVIEW)

**Checked:**
- [x] `deploy/scripts/lib/templates.sh`: `NGINX_HTTP2=on` → exit 2 naming BLK-013; any other value except `off` → exit 2; `off` renders `listen 443 ssl;` with no `http2` (BLK-013, ADR-015)
- [x] `deploy/scripts/deploy.sh`: the dirty-tree check covers `backend frontend deploy Makefile`; refuses with the list of dirty top-level paths unless `--allow-dirty`; `REVISION` records `dirty`, `dirty_paths`, `dirty_checked`; the release content is still `git archive <sha> backend` + locally built `dist`
- [x] `deploy/README.md` and root `.env.example` wording matches (http2 must be off; the dirty check scope; never `--allow-dirty` for the release of record)
- [x] No secrets; scope limited to the two phase-1 fixes plus docs

**Commands run:**
```
bash -n + shellcheck -x on all scripts                                → OK / clean
NGINX_HTTP2=on  render-templates.sh                                   → "NGINX_HTTP2=on is refused (BLK-013) …" EXIT 2
NGINX_HTTP2=yes render-templates.sh                                   → "NGINX_HTTP2 must be off (BLK-013)" EXIT 2
render-templates.sh (off)                                             → EXIT 0; no "http2" in any rendered nginx file
make deploy DRY_RUN=1 (with the uncommitted review changes present)   → "uncommitted change(s) in backend,deploy (6 path(s)) — commit them or use --allow-dirty" EXIT 2
```

**Before the live phase:** the orchestrator commits the reviewed changes (TASK-016, the TASK-012 fix, phase 1 and the `.ai` updates), so `make deploy` runs from a clean tree without `--allow-dirty`. The remaining TASK-014 notes (http2 evidence against dental, https health after `make tls`, the dental guard around certbot) still apply.

## QA Log

## Sign-off
- TL final review: ☐
- QA verdict: ☐
- PM acceptance: ☐
