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

READY_FOR_RELEASE

## Activity Log
- 2026-09-27 | team-lead | — → TODO | created for FEAT-004; starts after TASK-013 + backend chain + TASK-007 reach READY_FOR_QA; plan pre-approved
- 2026-09-27 | team-lead | TODO → TODO | amended from the TASK-012 review: permission evidence, `/static/` 200 check, `LETSENCRYPT_EMAIL` optional
- 2026-09-27 | team-lead | TODO → TODO | amended from the backend/QA reviews: journald token check + query-string log check, `qa_inactive` seeding
- 2026-09-27 | infrastructure | TODO → IN_PROGRESS | phase 1 (pre-live fixes, no live apply): NGINX_HTTP2=on refused (exit 2), dirty-tree check extended to deploy/ + Makefile (recorded in REVISION); waiting for the orchestrator's commit + go for the live phase
- 2026-09-27 | infrastructure | IN_PROGRESS → IN_PROGRESS | GO received (f85848b, clean tree); live phase: setup-server, deploy 205208, tls, health, seed-qa-users, --with-e2e, deploy 205632, rollback with DB restore, roll-forward 205803, crash test; every dental guard IDENTICAL
- 2026-09-28 | infrastructure | IN_PROGRESS → READY_FOR_REVIEW | live deployment done; report .ai/reports/infrastructure/FEAT-004-deployment-report.md (+ FEAT-004-deploy-logs/)
- 2026-09-27 | team-lead | IN_PROGRESS → IN_PROGRESS | phase 1 (pre-live fixes) reviewed and APPROVED; live phase may start after the orchestrator's commit
- 2026-09-28 | team-lead | READY_FOR_REVIEW → REVIEW | review of the live execution evidence
- 2026-09-28 | team-lead | REVIEW → READY_FOR_QA | APPROVED; finding 1 routed to TASK-017 (before TASK-015's rollback step); QA via TASK-015
- 2026-09-28 | qa | READY_FOR_QA → QA_IN_PROGRESS | FEAT-004 verification on the server started (TASK-015)
- 2026-09-28 | qa | QA_IN_PROGRESS → QA_IN_PROGRESS | QA verdict PASS ticked; status left for TL final review (.ai/reports/qa/FEAT-004-qa-report.md; release 20260927-232246 (d6669b6); runs 20260927-233545-139616, -233803-141021, -233920-141829, -233518-139162)
- 2026-09-28 | team-lead | QA_IN_PROGRESS → READY_FOR_RELEASE | TL final review signed off (QA PASS in FEAT-004-qa-report.md)

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
- **Report:** `.ai/reports/infrastructure/FEAT-004-deployment-report.md`. Raw logs (token-free, verified on the server) are in `.ai/reports/infrastructure/FEAT-004-deploy-logs/`.
- **Live:** https://delivery.hossam-ameen.online/ (PWA) and https://api.delivery.hossam-ameen.online/ (`/api/status/`, `/api/health/` + `/ready/` with the header token, `/admin/`, `/static/`). Release of record **20260927-205803**, sha `f85848b`, `dirty=false`.
- **Files changed (phase 1, reviewed):** `deploy/scripts/lib/templates.sh` (`NGINX_HTTP2=on` → exit 2), `deploy/scripts/deploy.sh` (dirty check covers `backend frontend deploy Makefile`; `REVISION` records `dirty`, `dirty_paths`, `dirty_checked`), `deploy/scripts/remote-test.sh` (the TASK-012 EXIT-trap fix), `deploy/README.md`, `.env.example`. Phase 2 changed no repo files except the reports.
- **Validation / acceptance evidence** (details in the report):
  - `setup-server`: `shared/.env` 0600 with server-generated secrets; unit installed and enabled; http bootstrap sites via safe-apply; `stat` modes shared 751 / db, backups, cache 700 / static, media 755; www-data checks ok and denied as expected.
  - First deploy from a clean commit: Python 3.13.15 venv, DB created by migrate, `current` switched, listener only on `127.0.0.1:8010`, HTTP health green.
  - `make tls`: one certificate `flash-delivery` for exactly the two names (no `-m`, the registered account was reused); TLS templates applied; 301 http→https on both; `renew --dry-run --cert-name flash-delivery` succeeded; the dental certificate and every dental file unchanged (guard IDENTICAL around certbot).
  - `make health` 8/8: https token health and ready, `/api/status/` 200, web 200, `/driver` 200, `/static/admin/css/nav_sidebar.css` **200** (not 403), HSTS without includeSubDomains/preload.
  - Secrets (counts on the server): token in the deploy logs 0, in the nginx flash logs 0, in journald 0. After a wrong-dummy `?password=` request: dummy value 0 and `password=` 0 in both the nginx logs and journald (path-only access logs).
  - BLK-013: 0 `http2` in the Flash files; `nginx -t` shows 0 `protocol options redefined`; dental negotiates HTTP/1.1 before and after (200 / 302).
  - `seed-qa-users`: qa_customer, qa_driver, qa_store, qa_admin (staff + superuser) and **qa_inactive (inactive)**; `credentials.env` 0600; passwords never printed.
  - `--with-e2e`: `install-deps` found all dependencies present, so apt made 0 upgrades and 0 new installs (dpkg 694 → 694); Chromium 1243 in `qa/browsers` (658 MB); disk 6.8 → 7.4 GB used.
  - **Rollback exercise:** deploy #2 (205632), then a marker user written after its pre-migrate backup, then `make rollback RESTORE_DB=always`. Result: `current` 205632 → 205208; unit stopped; live DB saved as `pre-rollback-*` (0600); backup restored; unit started; health 8/8. The marker was gone and the 5 QA users were intact, so the restore happened. The `auto` plan correctly said "no restore" (no migrations applied). Roll-forward: `make deploy` → 205803, health green.
  - Crash recovery: SIGKILL → back active and serving 200 in 5.8 s, NRestarts 1, enabled. No reboot.
  - Resources: flash-backend 91 MB / 700 MiB, Tasks 6/128, RAM available 3090 MB, disk 11 GB free; 3 releases (75 + 22 + 22 MB), 3 backups.
  - Dental: **every** guard compare was IDENTICAL; the final compare against the pre-deploy baseline is IDENTICAL; `dental-clinic-backend` active, MainPID 18284 unchanged, NRestarts 0; dental 200 / api.dental 302. `make throttle-reset` done at the end.
- **Contract/OpenAPI changes:** none.
- **Known limitations / remaining problems:**
  1. **The default manual rollback target is the previous release *id*, not deploy history.** After rollback + roll-forward, a bare `make rollback` would pick 205632 (the release rolled back from). `deploy.sh`'s auto-rollback passes the true previous release, so it is correct. Workaround: `make rollback TO=<id>`. Proposed fix (TL decision): record `PREVIOUS` at switch time and use it as the default target.
  2. The DB-restore path was exercised with `RESTORE_DB=always`, since no migration has been applied since the first release; the `auto` decision logic was shown in the plan.
  3. Local build machine: `npm ci` warns `EBADENGINE` (abbrev@5 / nopt@10 want node ≥ 24.15; local 24.3.0). The build is fine; upgrading the local Node is recommended.
  4. Two `/tmp/flash-nginx-backup-*` recovery copies are left on the server (the pre-setup and pre-TLS Flash files); they are harmless and can be removed.

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

### Review — 2026-09-28 — team-lead — execution evidence

**Verdict:** APPROVED

**Checked (report + raw logs + TL read-only checks; no deploy/rollback/restart by the TL — QA TASK-009/010 running):**
- [x] Every AC has evidence in `.ai/reports/infrastructure/FEAT-004-deployment-report.md` and `FEAT-004-deploy-logs/00…12`
- [x] Release of record `20260927-205803` from `f85848b`, `dirty=false`, `dirty_checked=backend frontend deploy Makefile` (REVISION read via `make status`)
- [x] Listener only on `127.0.0.1:8010`; unit enabled; permissions per ADR-015 (shared 751; db/backups/cache 700; static/media 755; `.env` and `qa/credentials.env` 600)
- [x] TLS: cert `flash-delivery` = exactly the two Flash names, valid to 2026-12-26; both sites on the TLS variant; HSTS `max-age=31536000` only
- [x] BLK-013: 0 `http2` in the Flash files, 0 `protocol options redefined` in `nginx -t`; Flash, dental and api.dental all answer on HTTP/1.1 (curl `--http2` offered): dental 200, api.dental 302, unchanged
- [x] Secrets: TL server-side counts (value never printed): health token in the committed-to-be reports/logs 0, in journald 0, in the Flash nginx logs 0; `QA_CUSTOMER_PASSWORD`/`QA_ADMIN_PASSWORD` in the reports 0
- [x] Dental: `dental-clinic-backend` active, MainPID 18284, NRestarts 0 (unchanged since the audit); every guard compare IDENTICAL per the logs
- [x] Rollback + DB restore (ADR-017) and crash recovery exercised; sudo use within the ADR-015 list

**Decisions on Infrastructure's findings:**
1. **Bare `make rollback` targets the previous id, not deploy history — a real defect; fix BEFORE QA's TASK-015 rollback step.** TASK-015 AC "`make rollback` → previous release serves" would otherwise exercise the wrong target on the live site (current 205803 → by-id 205632 instead of the actually-previous 205208). Created **TASK-017** (Infrastructure): record `PREVIOUS` at every switch; a bare rollback uses it and refuses (exit 2, asks for `TO=`) when it is missing; prune keeps current + recorded previous; one-time backfill `releases/20260927-205803/PREVIOUS = 20260927-205208` (confirmed from `09b-rollback-live.txt`/`10-deploy3.txt`). ADR-013 clarified. TASK-015 now depends on TASK-017 for its rollback step only; until then everyone uses `make rollback TO=<id>`. Not blocking for TASK-014: the deploy auto-rollback passes the explicit id and was correct.
2. **DB restore exercised with `always`, not `auto` — ACCEPTED.** The restore mechanics (stop → pre-rollback copy → restore → start → health, marker gone, QA users intact) are proven; `auto` correctly chose "no restore" because no migration was applied. The `auto` + applied-migration path gets live evidence at the first deploy whose release applies a migration (Infrastructure records it in that deploy's report; QA covers it in the next FEAT-004 regression).
3. **Local Node 24.3 `EBADENGINE` warnings — ACCEPTED, non-blocking.** They come from dev-only transitive deps (abbrev/nopt via js-beautify); the project's `engines.node` is satisfied and the build is green. Recommendation to the operator: move the build machine to Node 24 ≥ 24.15 (or 22 LTS). No task.
4. **Two `/tmp/flash-nginx-backup-*` on the server — ACCEPTED as harmless** (outside `/etc/nginx`, Flash files only). Removal plus "delete the backup after a successful safe-apply" is part of TASK-017.

**Commands run (TL, read-only):**
```
make health   → 8/8 PASS (unit, local health + ready, public health + ready with header token, /api/status/, web root, nginx -t)  EXIT 0
make status   → current 20260927-205803; releases 205208 205632 205803; REVISION sha f85848b… dirty=false; 3 backups;
                both Flash sites variant=tls; cert flash-delivery covers both names, expiry 2026-12-26; flash-backend 96.7 MB, NRestarts 1 (the crash test)
ssh (read-only): ss :8010 → 127.0.0.1 only; stat modes as above; is-enabled flash-backend = enabled; dental active MainPID 18284 NRestarts 0;
                nginx -t "protocol options redefined" count 0; http2 in Flash site files 0/0; /tmp/flash-nginx-backup-* ×2 present;
                curl --http2: dental 200 1.1, api.dental 302 1.1, flash /driver 200 1.1, /static/admin/css/nav_sidebar.css 200; api HSTS max-age=31536000
secret counts on the server (reports tar-streamed to a /tmp dir and removed): token 0 / journald 0 / flash nginx logs 0; QA passwords in reports 0
```

### Review — 2026-09-28 — team-lead — final

**Verdict:** APPROVED — TL final sign-off.
- QA evidence: `.ai/reports/qa/FEAT-004-qa-report.md` (PASS). The deployment report `.ai/reports/infrastructure/FEAT-004-deployment-report.md` stands; the final release is now `20260927-232246` from the roll-forward.
- No repo changes after the TL review of phase 1 other than the reviewed BUG-002/TASK-017 changes.
- Live state checked read-only by the TL: `make status` → current `20260927-232246` (`d6669b6`, dirty=false), previous `20260927-205208` (from PREVIOUS), flash-backend active, NRestarts 0; `make health` ALL CHECKS PASSED; dental-clinic-backend active, MainPID 18284, NRestarts 0.

## QA Log
- 2026-09-28 | qa | IN PROGRESS | live checks PASS (smoke/deploy run 20260927-230332-114972, make health); rollback exercise pending (permission)
- 2026-09-28 | qa | PASS | .ai/reports/qa/FEAT-004-qa-report.md; release 20260927-232246 (d6669b6); runs 20260927-233545-139616, -233803-141021, -233920-141829, -233518-139162

## Sign-off
- TL final review: ☑ (team-lead, 2026-09-28)
- QA verdict: ☑ PASS (.ai/reports/qa/FEAT-004-qa-report.md; release 20260927-232246 (d6669b6); runs 20260927-233545-139616, -233803-141021, -233920-141829, -233518-139162)
- PM acceptance: ☐
