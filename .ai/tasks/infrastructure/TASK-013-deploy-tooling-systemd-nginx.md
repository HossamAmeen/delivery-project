# Task

## ID
TASK-013

## Title
Deploy tooling: systemd/nginx templates, deploy/migrate/restart/health/rollback/tls scripts, Makefile, README (systemd mode)

## Feature
FEAT-004 — Deployment & Environments

## Description
Build and validate the complete operator tooling for the systemd single-server deployment defined in ADR-013/015/016/017, on top of TASK-012's library. This task **creates and validates** the tooling (locally + read-only/temporary checks on the server); it does **not** change the live nginx/systemd/certbot state — that is TASK-014.

## Business Requirement
REQ-008; BLK-011 (RESOLVED); DRF_SKILL.md §41–53, §70–74; ADR-012, ADR-013, ADR-015, ADR-016, ADR-017, ADR-019; FEAT-004 criteria 1–3, 5–8, 10–12

## Agent
Infrastructure

## Scope (allowed paths)
- `deploy/scripts/**` (deploy.sh, deploy-backend.sh, deploy-frontend.sh, restart.sh, restart-backend.sh, restart-frontend.sh, migrate.sh, collectstatic.sh, health-check.sh, rollback.sh, tls.sh, prune.sh, seed-qa-users.sh, render-templates.sh; extend setup-server.sh and lib/*)
- `deploy/nginx/api.conf.template`, `deploy/nginx/web.conf.template`, `deploy/nginx/api.http.conf.template`, `deploy/nginx/web.http.conf.template`
- `deploy/systemd/backend.service.template`
- `deploy/env/shared.env.template`
- root `Makefile`, root `.env.example`, `deploy/README.md` (all sections), `.ai/reports/infrastructure/**`

## Dependencies
- TASK-012 (library, layout, uv)
- Build/runtime contracts: TASK-001 (`backend/requirements/production.txt`, `config.wsgi`, env names in `backend/.env.example`), TASK-007 (`npm ci && npm run build` → `frontend/dist`, `VITE_API_BASE_URL`), api-contracts § Foundation (health endpoints). Coding can start now from these written contracts; the final dry-run against the real `backend/`/`frontend/` happens when they exist.
- Runs **in parallel** with the backend chain and TASK-007.

## Acceptance Criteria
- [ ] **Make targets** (root `Makefile`, all delegating to `deploy/scripts/*`, all accepting `DRY_RUN=1`): `deploy`, `restart [TARGET=backend|frontend|all]`, `migrate`, `health`, `rollback [RESTORE_DB=auto|always|never]`, `tls`, `setup-server`, `seed-qa-users`, `logs` (tail journald for the Flash unit), `status`, plus TASK-012's targets. `make help` lists them.
- [ ] **Templates** rendered only through `render-templates.sh` with `envsubst` and an **explicit variable list** (nginx `$host`, `$uri`, … survive). Rendered nginx matches ADR-015 exactly: two files named `${API_DOMAIN}` and `${WEB_DOMAIN}`; API: `/static/`, `/media/` aliases to `shared/`, proxy to `127.0.0.1:${BACKEND_PORT}` with `X-Forwarded-For $remote_addr` (overwrite), `X-Forwarded-Proto $scheme`, `Host $host`, `client_max_body_size 10m`, `log_format flash_api` without query strings; Web: `root ${DEPLOY_PATH}/current/frontend/dist`, SPA fallback, cache headers per ADR-015; both: 80 → ACME + 301, 443 `ssl` (no `http2`: BLK-013 RESOLVED, ADR-015) with `/etc/letsencrypt/live/${CERT_NAME}/…`, HSTS without `includeSubDomains`/`preload`. `.http.conf` bootstrap variants serve port 80 only (ACME + SPA/proxy) until the cert exists.
- [ ] **systemd unit** rendered from `backend.service.template` exactly per ADR-015 (User/Group, WorkingDirectory, EnvironmentFile, gunicorn ExecStart with the env-driven workers/threads/timeout, Restart=always, MemoryMax, TasksMax, hardening, `ReadWritePaths=${DEPLOY_PATH}/shared`). **Access log without query strings** (added 2026-09-27, backend review; ADR-015 amended): gunicorn gets an `--access-logformat` that uses `%(U)s` (path only) and never `%(r)s`/`%(q)s`, e.g. `%({x-forwarded-for}i)s %(t)s "%(m)s %(U)s %(H)s" %(s)s %(b)s %(D)sus "%(a)s"`; every `%` is escaped as `%%` in the unit (systemd specifiers) — or the format lives in a rendered gunicorn config file. Evidence: the rendered `ExecStart` (or config) and `systemd-analyze verify` clean of specifier errors.
- [ ] **`shared.env.template`**: all variables of `backend/.env.example` with the server values from ADR-015/017 (`DJANGO_SETTINGS_MODULE=config.settings.production`, `DEBUG=False`, SQLite `DATABASE_URL`, `RATELIMIT_CACHE_URL=filecache:///srv/flash/shared/cache`, `CELERY_ENABLED=False`, `NUM_PROXIES=1`, `SECURE_PROXY_SSL_HEADER`, hosts/CORS/CSRF, static/media roots, `API_DOCS_PUBLIC=False`, JWT lifetimes, rate limits) and placeholders `__GENERATE__` for `SECRET_KEY` and `HEALTH_CHECK_PASSWORD`. `NUM_PROXIES=1` is required (nginx overwrites `X-Forwarded-For`, ADR-015). Backend's optional names (`DB_CONN_MAX_AGE`, `LOG_LEVEL`, `LANGUAGE_CODE`, `TIME_ZONE`, `SECURE_HSTS_INCLUDE_SUBDOMAINS`, `SECURE_HSTS_PRELOAD`, `API_PAGE_SIZE`, `API_MAX_PAGE_SIZE`, `JWT_ROTATE_REFRESH_TOKENS`) may be listed with their defaults; **`FLASH_NEW_USER_PASSWORD` (command-only) and `DJANGO_ENV_FILE` (local/tests only) must not be in `shared/.env`**; `SECURE_HSTS_INCLUDE_SUBDOMAINS`/`PRELOAD` stay False (the parent domain is shared with dental). `setup-server.sh` (full) renders it to `shared/.env` **only if absent**, generates the two secrets on the server, `chmod 600`; if present, it only reports missing keys (never overwrites).
- [ ] **Directory permissions (TL decision 2026-09-27, TASK-012 review; ADR-015 § Layout "Permissions"):** `setup-server.sh` sets and verifies, idempotently (existing dirs are fixed, not recreated): `/srv/flash` 0755, `releases/` 0755, **`shared/` 0751**, `shared/{static,media}` 0755, **`shared/{db,backups,cache}` 0700**, `shared/logs` 0750, `shared/.env` 0600, `sandbox/` and `qa/` 0750, all `hossam:hossam`. No `www-data` group ownership. Validation evidence: `sudo -u www-data test -r ${DEPLOY_PATH}/shared/static/.` succeeds and `sudo -u www-data ls ${DEPLOY_PATH}/shared` and `… test -r ${DEPLOY_PATH}/shared/db/.` fail (read-only checks).
- [ ] **`setup-server.sh` full** (idempotent, guarded): bootstrap (TASK-012) → `shared/.env` → render + `sudo install` the unit to `/etc/systemd/system/${BACKEND_SYSTEMD_SERVICE}.service` → `sudo systemctl daemon-reload` + `enable` (start only when `current` exists) → install the nginx site files (http bootstrap variant if the cert is missing, full variant otherwise) via the **nginx safe-apply** function → optional `--with-e2e` (Playwright Chromium + `install-deps`, disk check first, package list logged).
- [ ] **nginx safe-apply** (one function, used everywhere): backup current Flash site files → write new → `sudo nginx -t` → on failure restore backup, `sudo nginx -t` again, exit non-zero **without reloading** → on success `sudo systemctl reload nginx`. Refuses any file name other than `${API_DOMAIN}`/`${WEB_DOMAIN}`. Never `restart`, never touches other files.
- [ ] **`tls.sh`**: runs exactly `sudo certbot certonly --nginx --cert-name ${CERT_NAME} -d ${API_DOMAIN} -d ${WEB_DOMAIN} --non-interactive --agree-tos [-m ${LETSENCRYPT_EMAIL}] --deploy-hook "nginx -t && systemctl reload nginx"`. **`LETSENCRYPT_EMAIL` is optional** (amended 2026-09-27, TASK-012 review, ADR-015 § TLS): when it is empty, omit `-m` and reuse the server's registered Let's Encrypt production account; fail early with a clear message only if it is empty **and** `sudo certbot show_account` finds no production account; never `--register-unsafely-without-email`. then switches both sites to the full template via safe-apply, then `sudo certbot renew --dry-run --cert-name ${CERT_NAME}`. Idempotent (skips issuance when the cert exists and covers both names).
- [ ] **`deploy.sh`** implements the ADR-015 order: preflight (env, mode, clean tree unless `--allow-dirty`, SSH reachable, disk ≥ `MIN_FREE_DISK_MB`, dental snapshot, port guard) → `deploy-frontend.sh` builds locally (`npm ci && npm run build` with `VITE_API_BASE_URL`) → stage `git archive` of `backend/` + `frontend/dist` + `REVISION` (sha, UTC time, dirty flag) → rsync to `releases/<UTC ts>` with `--link-dest` → `deploy-backend.sh` on the server (uv venv 3.13, `uv pip install -r backend/requirements/production.txt`, `check --deploy` (warnings logged), `collectstatic --noinput`) → `migrate.sh` (ADR-017 backup + `MIGRATION_STATE`) → atomic `current` switch → restart backend → nginx safe-apply only if rendered files differ → `health-check.sh` with retries up to `HEALTH_CHECK_TIMEOUT` → dental compare → `prune.sh` (keep `RELEASES_TO_KEEP` releases, never the current or previous; `DB_BACKUPS_TO_KEEP` backups) → summary (release id, sha, duration, health result). On a failure after the switch: `AUTO_ROLLBACK=true` → `rollback.sh`, exit non-zero, print the rollback outcome; before the switch: remove the half-built release, exit non-zero, site untouched.
- [ ] **`migrate.sh`** standalone (`make migrate`) = backup + migrate for `current`, same ADR-017 rules; uses `--plan` first and prints the planned migrations.
- [ ] **`rollback.sh`**: target = previous release (or `--to <id>`); ADR-017 DB restore logic (`ROLLBACK_RESTORE_DB`, `--restore-db`/`--no-restore-db`, pre-rollback DB copy, loss warning); switch → restart → health → dental compare. Fails clearly if no previous release exists.
- [ ] **`restart.sh backend|frontend|all`**: backend = `sudo systemctl restart ${BACKEND_SYSTEMD_SERVICE}` + wait for health; frontend = re-render/safe-apply the web site + reload (no process); all = both.
- [ ] **`health-check.sh`** per ADR-015 (runs on the server; 127.0.0.1 and public HTTPS; header token via `curl -H @-` from `shared/.env`; frontend root 200 + app root marker; `systemctl is-active`; `sudo nginx -t`). Never prints the token; exit non-zero on any failure with the failing check named.
- [ ] **`seed-qa-users.sh`**: generates random passwords on the server, runs `manage.py create_role_user … --password-stdin --update` in `current` with `shared/.env` loaded, writes `/srv/flash/qa/credentials.env` (0600) with `QA_<ROLE>_USERNAME/PASSWORD`; prints usernames only. Users: `qa_customer`, `qa_driver`, `qa_store`, `qa_admin` (`--role ADMIN --staff --superuser`) **and `qa_inactive`** (added 2026-09-27 from QA TASK-008: `--role CUSTOMER --inactive`, exported as `QA_INACTIVE_USERNAME` / `QA_INACTIVE_PASSWORD`). The `--inactive` flag comes from Backend TASK-016; until it is merged, the script must detect its absence (`create_role_user --help`) and skip `qa_inactive` with a warning rather than fail.
- [ ] **Validation evidence** (Completion Report): `bash -n` + `shellcheck` clean; `--dry-run` of every script/target in `systemd` mode (redacted), and `DEPLOYMENT_MODE=docker` / missing mode fail with the documented exit code; templates rendered locally with the real `.env.example` values; rendered nginx validated **on the server without touching the live config**: `sudo nginx -t -c /tmp/flash-nginx-test/nginx.conf` with a minimal temp `nginx.conf` that includes only the rendered Flash files, temp pid/error_log paths, and a temp self-signed cert substituted for the LE paths; rendered unit checked with `systemd-analyze verify` on the server (document any "executable not found" warning caused by the not-yet-existing release); `grep` proof that no secret literal is in `deploy/`, `Makefile`, `.env.example`.
- [ ] `deploy/README.md` complete per FEAT-004 AC12: server requirements, SSH setup, env variables (both files), systemd mode, nginx/TLS, every command with examples, health, rollback (incl. DB restore semantics), co-hosting rules with dental, resource limits/retention, remote testing, troubleshooting (nginx -t failure, health failure, disk full, locked SQLite).

## Technical Notes — pre-approved constraints (TL, 2026-09-27)
- ADR-015 is the spec. The hard rules: only the two Flash nginx files; `nginx -t` before every reload (safe-apply); never `nginx -s reload`/`systemctl restart nginx`; certbot only `certonly --nginx --cert-name ${CERT_NAME}` with the two `-d`; never `certbot renew` without `--cert-name` (except `--dry-run` scoped); never anything under `/srv/dental-clinic`, dental's unit or port 8000; no Docker; no builds on the server.
- `sudo` writes are limited to: `/srv/flash` creation, `/etc/systemd/system/${BACKEND_SYSTEMD_SERVICE}.service`, `/etc/nginx/sites-available/${API_DOMAIN|WEB_DOMAIN}` + their `sites-enabled` symlinks, certbot for `${CERT_NAME}`, `systemctl daemon-reload|enable|restart|stop|start|kill ${BACKEND_SYSTEMD_SERVICE}` (`stop|start` added 2026-09-27 in the TL review: needed by the ADR-017 DB restore on rollback; Flash unit only), `systemctl reload nginx` (after `nginx -t`), and (`--with-e2e` only) Playwright's `install-deps`.
- **From the TASK-012 review (2026-09-27):**
  - The dental guard hashes **every** file under `/etc/nginx/` except the two Flash site files. So safe-apply backups, temp renders and test configs must **never** be written anywhere under `/etc/nginx/` (keep them under `${DEPLOY_PATH}` or `/tmp/flash-*`), or the guard fails and nginx might load them. The guard also hashes `/etc/letsencrypt/options-ssl-nginx.conf`; if `tls.sh` trips it there, stop and report to the TL (do not widen the guard's exclusions on your own).
  - Use `remote_fn rw` (not `ro` + an `apply` flag) for every new state-changing remote call, so `--dry-run` is enforced by the transport.
  - `lib/*.sh` and the runner are approved as delivered; extend them rather than duplicating helpers.
- Forward-only migrations (ADR-013); the DB restore on rollback is the SQLite exception (ADR-017).
- The docker branch of every script = clear "deferred" error; do not create `deploy/docker/**` or compose files.
- `.github/workflows/deploy.yml` is out of scope (BLK-012).
- If the app needs a change for deployability, raise it to the TL (do not edit `backend/` or `frontend/`).

## Testing Requirements
- As in the validation criterion above. No live nginx/systemd/certbot change in this task.
- 2026-09-28 | infrastructure | IN_PROGRESS → READY_FOR_REVIEW | BUG-002 fixed in the API templates (proxy_hide_header X-Content-Type-Options in location /; http variant also gets the server-level nosniff); isolated nginx -t + functional header count on the server; no live apply (ships with the next make deploy)

## Plan Review Required
Yes — production deployment, nginx, systemd, TLS on a shared server. **Pre-approved** by the TL on 2026-09-27 against ADR-015/016/017 and the constraints above: write `.ai/reports/infrastructure/FEAT-004-infra-design.md` (short: script responsibilities, variable list, safe-apply and rollback flow diagrams) and a ≤ 20-line `## Implementation Plan`, then proceed without waiting. Deviations from ADR-015 need TL approval first. The TL reviews the implementation (infrastructure.md §6 validation list).

## Status

DONE

## Activity Log
- 2026-09-27 | team-lead | — → TODO | created for FEAT-004 (ADR-015/016/017); runs in parallel with backend/frontend; plan pre-approved
- 2026-09-27 | team-lead | TODO → TODO | amended from the TASK-012 review: `shared/` 0751 permission scheme (ADR-015), `LETSENCRYPT_EMAIL` optional (omit `-m`, reuse the account), guard/safe-apply notes
- 2026-09-27 | team-lead | TODO → TODO | amended from the backend/QA reviews: gunicorn access log without query strings, `shared.env` variable rules (`NUM_PROXIES=1`, no `FLASH_NEW_USER_PASSWORD`/`DJANGO_ENV_FILE`), `qa_inactive` in `seed-qa-users` (TASK-016)
- 2026-09-27 | infrastructure | TODO → IN_PROGRESS | started; design note .ai/reports/infrastructure/FEAT-004-infra-design.md
- 2026-09-27 | infrastructure | IN_PROGRESS → IN_PROGRESS | permission scheme applied on the server via `setup-server --bootstrap-only` (www-data checks pass); raised BLK-013 (nginx http2 is socket-wide on 1.24 → would change dental), NGINX_HTTP2=off by default
- 2026-09-27 | infrastructure | IN_PROGRESS → READY_FOR_REVIEW | tooling complete and validated without live nginx/systemd/certbot changes; evidence .ai/reports/infrastructure/TASK-013-validation-2026-09-27.md
- 2026-09-27 | team-lead | READY_FOR_REVIEW → REVIEW | code review started
- 2026-09-27 | team-lead | REVIEW → READY_FOR_QA | code review APPROVED (Review Log); BLK-013 RESOLVED (http2 off); sudo stop|start confirmed; live execution in TASK-014, QA via TASK-015
- 2026-09-28 | qa | READY_FOR_QA → QA_IN_PROGRESS | FEAT-004 verification on the server started (TASK-015)
- 2026-09-28 | team-lead | QA_IN_PROGRESS → IN_PROGRESS | BUG-002 (Low) routed to Infrastructure: `proxy_hide_header X-Content-Type-Options` in the proxied API location; constraints in BUG-002 § Routing; QA of the rest continues in TASK-015
- 2026-09-28 | team-lead | READY_FOR_REVIEW → REVIEW | BUG-002 fix review
- 2026-09-28 | team-lead | REVIEW → READY_FOR_QA | BUG-002 fix APPROVED incl. the http-variant deviation; ships with TASK-015's roll-forward deploy; QA re-test TC-001-SEC-03 + TASK-015
- 2026-09-28 | qa | READY_FOR_QA → QA_IN_PROGRESS | BUG-002 re-test and deploy/rollback evidence on release 20260927-232246
- 2026-09-28 | qa | QA_IN_PROGRESS → QA_IN_PROGRESS | QA verdict PASS ticked; status left for TL final review (.ai/reports/qa/FEAT-004-qa-report.md; release 20260927-232246 (d6669b6); runs 20260927-233545-139616, -233803-141021, -233920-141829, -233518-139162)
- 2026-09-28 | team-lead | QA_IN_PROGRESS → READY_FOR_RELEASE | TL final review signed off (QA PASS in FEAT-004-qa-report.md; BUG-002 VERIFIED)
- 2026-09-28 | project-manager | READY_FOR_RELEASE → DONE | FEAT-004 accepted against the DoD (.ai/reports/pm/sprint-01-acceptance-2026-09-28.md)

## Implementation Plan
1. Design note `.ai/reports/infrastructure/FEAT-004-infra-design.md` (script map, variables, safe-apply / deploy / rollback flows).
2. Templates: `deploy/nginx/{api,web}{,.http}.conf.template`, `deploy/systemd/backend.service.template` (access log `%%(U)s`, `%` escaped), `deploy/env/shared.env.template` (backend/.env.example names, server values, `__GENERATE__`).
3. `lib/templates.sh` + `render-templates.sh` (envsubst with an explicit list; unresolved/empty variable → exit 2); `lib/server.sh` = shared remote functions (stage receive, shared-env loader, nginx safe-apply, switch, migrate/backup, health, prune) and `lib/ops.sh` local helpers (op lock, guard nesting via `FLASH_GUARD_ACTIVE`).
4. Scripts: setup-server (full + `--bootstrap-only`, `--with-e2e`, new permission modes, verify), deploy, deploy-frontend, deploy-backend, collectstatic, migrate, restart(+backend/frontend), health-check, rollback, tls, prune, seed-qa-users. Every state change goes through `remote_fn rw`/`run` (dry-run enforced by the transport); read-only probes through `ro`.
5. Makefile targets + `make help`; `.env.example` additions if needed; full `deploy/README.md`.
6. Validate: `bash -n` + shellcheck; docker/missing mode → exit 2 for every script; `--dry-run` of every script/target; local render with `.env.example`; server-side isolated `nginx -t -c /tmp/flash-nginx-test/nginx.conf` (temp self-signed cert) and `systemd-analyze verify` of the rendered unit under `/tmp/flash-*`; ExecStart argv parse check on the LOCAL user manager; permissions applied via `setup-server --bootstrap-only` + www-data read checks; shared.env first-render/missing-key logic against a `/tmp/flash-*` target; scratch-copy frontend build via `deploy-frontend.sh`; secret-literal grep; dental before/after. **No live nginx/systemd/certbot change** (TASK-014).

## Completion Report
- **Files changed:**
  - templates: `deploy/nginx/{api,web}.conf.template`, `deploy/nginx/{api,web}.http.conf.template`, `deploy/systemd/backend.service.template`, `deploy/env/shared.env.template`
  - libs: `deploy/scripts/lib/templates.sh`, `lib/server.sh` (all server-side `_fs_*` functions), `lib/ops.sh` (op lock, nested dental guard, staging, `ops_remote`). `lib/common.sh`, `lib/dental_guard.sh` and `remote-test.sh` are unchanged.
  - scripts: `render-templates.sh`, `deploy.sh`, `deploy-frontend.sh`, `deploy-backend.sh`, `migrate.sh`, `collectstatic.sh`, `restart.sh`, `restart-backend.sh`, `restart-frontend.sh`, `health-check.sh`, `rollback.sh`, `tls.sh`, `prune.sh`, `seed-qa-users.sh`, `status.sh` (status/logs), `setup-server.sh` (full phase + `--bootstrap-only` + `--with-e2e` + new modes + verify), `deploy/scripts/.shellcheckrc`
  - root `Makefile` (deploy, restart TARGET=, migrate, collectstatic, health, rollback TO=/RESTORE_DB=, tls, prune, seed-qa-users, render, logs, status, setup-server BOOTSTRAP_ONLY=/WITH_E2E=, plus the TASK-012 targets; all accept `DRY_RUN=1`); root `.env.example` (+`NGINX_HTTP2=off`); `deploy/README.md` (all sections, FEAT-004 AC12)
  - `.ai/reports/infrastructure/FEAT-004-infra-design.md`, `.ai/reports/infrastructure/TASK-013-validation-2026-09-27.md`, `.ai/planning/blockers/BLK-013-nginx-http2-shared-socket.md`
  - local git-ignored `.env`: `NGINX_HTTP2=off` appended
  - server (live): only the `/srv/flash` permission modes (TL decision). No unit, no nginx file, no certbot change, and no `shared/.env` (verified: counts 0)
- **Tests added:** none in the repo. Validation harnesses (safe-apply, shared.env, pipeline) lived in the scratchpad and used the real library functions against `/tmp/flash-*`.
- **Validation commands run + results** (full output: `.ai/reports/infrastructure/TASK-013-validation-2026-09-27.md`):
  - `bash -n` on 22 files OK. `shellcheck -x` clean.
  - docker / empty / invalid mode × 17 scripts: 51/51 exit 2.
  - Local render from `.env.example`: nginx variables survive; `shared.env` keys = `backend/.env.example` minus `FLASH_NEW_USER_PASSWORD` and `DJANGO_ENV_FILE`.
  - `ExecStart` argv parsed by systemd (local user manager): exact path-only access format. `systemd-analyze verify` on the server: only the expected "gunicorn not executable yet"; 0 specifier errors.
  - `sudo nginx -t -c /tmp/flash-nginx-test/…`: isolated http and full variants OK. A combined test with live dental sites is OK and warning-free with `NGINX_HTTP2=off` (it warns with http2 on; BLK-013).
  - nginx safe-apply, 5 cases in test mode: install, unchanged, broken → restore + no reload (hashes identical), foreign name refused, first-install failure → removed.
  - Permissions applied and verified: www-data can read static/media, is denied on `ls shared`, `db`, `backups` and `.env`. Idempotent re-run.
  - `shared.env`: created once (0600, secrets generated server-side, never printed), never overwritten, missing keys reported.
  - Pipeline test on the real backend under `/tmp/flash-rbtest`: venv 3.13.15, `check --deploy` (W004/W008 only), collectstatic, migrate (first: no backup, applied=yes; second: backup, applied=no), switch, `--link-dest` hardlinks, rollback plans (auto/always/never plus the no-previous refusal), prune.
  - `DRY_RUN=1` of every target recorded. Local scratch frontend build via `deploy-frontend.sh` OK (28 files, API URL baked in).
  - Secret grep clean. Dental before/after IDENTICAL. Runners still work after the mode change.
- **Contract/OpenAPI changes:** none.
- **Decisions / deviations for TL review:**
  1. **BLK-013:** `NGINX_HTTP2` defaults to `off`. On nginx 1.24, `listen … http2` is socket-wide and would switch dental's 443 to HTTP/2, which conflicts with ADR-015's non-interference rule. `on` is one variable away. The TL decides before TASK-014.
  2. Health before the certificate exists: public checks use http and **skip** the token endpoints (the token is never sent over plain HTTP). Without this, the first deploy (which happens before `make tls`) would always fail health and auto-roll back with nothing to roll back to.
  3. The rollback DB restore uses `sudo systemctl stop|start flash-backend` (ADR-017's wording). These verbs are not in TASK-013's sudo list (`daemon-reload|enable|restart|kill`).
  4. The SQLite online backup and restore use the system `python3` (stdlib `sqlite3`), not the release venv.
  5. The safe-apply test mode (`FLASH_NGINX_ROOT=/tmp/flash-*`, no reload) exists for validation only; no operator script sets it.
  6. `setup-server --bootstrap-only` was added and used to apply the permission scheme without touching nginx or systemd.
  7. The dirty-tree check covers `backend/` and `frontend/` only (the release content), not `.ai/`.
- **Known limitations / remaining problems:**
  - Not exercised live (TASK-014 scope): the real unit install and start, nginx install and reload, certbot issuance and renew dry-run, a real deploy with health, a live rollback with DB restore, `seed-qa-users` (needs a release), and `--with-e2e` (apt).
  - `make deploy` without `ALLOW_DIRTY=1` refuses until `backend/` and `frontend/` are committed (HEAD `8b5dc17` has neither). The orchestrator must commit before TASK-014.
  - For Backend (FYI, harmless): collectstatic reports a duplicate `admin/js/popup_response.js` (jazzmin vs admin).
  - `certbot certonly --nginx` temporarily edits the Flash site file during the challenge and reverts it. The dental guard will show whether it touches anything else (e.g. `options-ssl-nginx.conf`); if it does, TASK-014 stops and reports to the TL, as instructed.
  - No remote `make` target was denied by the permission policy during this task.

### Fix — 2026-09-28 — BUG-002 (duplicate `X-Content-Type-Options` on proxied API responses)
- **TL decision (BUG-002 § Routing):** keep nginx's server-level `add_header X-Content-Type-Options "nosniff" always;` and hide the upstream (Django) copy in the proxied location. Django is unchanged.
- **Changes:**
  - `deploy/nginx/api.conf.template`: `proxy_hide_header X-Content-Type-Options;` in `location /`.
  - `deploy/nginx/api.http.conf.template`: the same `proxy_hide_header` in `location /`, **plus** the server-level `add_header X-Content-Type-Options "nosniff" always;`. The bootstrap variant had no nginx-level nosniff, so hiding the upstream copy alone would have left **zero** headers. With both, it is exactly one in both variants.
  - No web-site template or script changes.
- **Validation** (no live apply):
  - Local render (`ENV_FILE=.env.example render-templates.sh`) exit 0; each API variant has 1 `proxy_hide_header` + 1 `add_header` for nosniff.
  - On the server, under `/tmp/flash-bug002` (removed afterwards):
    - `sudo nginx -t -c …` on the isolated **http** and **full** API variants → syntax ok / successful
    - **combined** test (live `nginx.conf` + live dental, default and Flash web sites + the NEW Flash API TLS file) → syntax ok / successful
  - Functional test: a temporary non-root nginx on 127.0.0.1:18080 ran the rendered API http variant (listen/upstream rewritten), in front of a throw-away upstream that sends `nosniff` like Django:
```
### functional (readiness-gated, status codes shown)
upstream direct (Django stand-in, sends nosniff): status=200 nosniff-count=1
via nginx, proxied /api/status/:                  status=200 nosniff-count=1
via nginx, /static/ missing file (nginx 404):     status=404 nosniff-count=1
via nginx, upstream down (nginx 502):             status=502 nosniff-count=1
cleanup: /tmp/flash-* left = 0; temp processes left = 0
live site (old template, for comparison): 2 nosniff headers on /api/status/
```
  - The first two functional attempts gave misleading 0 counts, caused by my harness (a root-owned log file from `sudo nginx -t` stopped the non-root nginx; then the upstream was not yet listening). The run above is readiness-gated and prints status codes.
- **Deployment:** it ships with the next `make deploy`. The rendered API file differs, so safe-apply runs `nginx -t` and reloads. That is TASK-015's roll-forward. QA re-tests BUG-002 afterwards (expected: exactly 1 header on `/api/status/`, `/api/health/`, `/static/…`).


## Review Log
- 2026-09-27 | team-lead | PLAN PRE-APPROVED (conditional) | valid within the Technical Notes constraints and ADR-015/016/017

### Review — 2026-09-27 — team-lead — code

**Verdict:** APPROVED

**Checked:**
- [x] Scope: `deploy/**`, root `Makefile`, root `.env.example`, `deploy/README.md`, infra reports, BLK-013; live server change limited to the `/srv/flash` permission modes (TL decision from the TASK-012 review)
- [x] Business rules / auth / state / money / migrations — n/a (forward-only migrate + ADR-017 backup/restore implemented as specified)
- [x] Contracts: health checks use the Foundation contract (header token via `curl -H @-`, `/api/status/`, web root `id="app"`)
- [x] Validation passes (below); the Infrastructure evidence (safe-apply 5 cases, permissions, shared.env idempotency, pipeline on `/tmp/flash-rbtest`, dry-runs, dental IDENTICAL) is consistent with the code
- [x] No hardcoded secrets/domains/ports/paths: everything from `.env`; `shared.env.template` has `__GENERATE__` placeholders only; `FLASH_NEW_USER_PASSWORD`/`DJANGO_ENV_FILE` excluded; `NUM_PROXIES=1`; HSTS subdomains/preload False
- [x] ADR-012/013/015/016/017 and the infra DoD: two Flash site files only, safe-apply (`nginx -t` → restore on failure, no reload), `certonly --nginx --cert-name`, scoped renew dry-run, unit per ADR-015 incl. path-only gunicorn access log with `%%` escaping, `UMask=0022` so media stays readable by nginx
- [x] `DEPLOYMENT_MODE` respected (docker/empty/invalid → exit 2 for all 17 scripts), systemd validated; rollback path implemented (auto/always/never, pre-rollback DB copy, refuses with no previous release)

**Decisions:**
1. **BLK-013 — option A, `NGINX_HTTP2=off`. RESOLVED.** The user's hard constraint (dental must not be affected) rules out B (switches dental to HTTP/2) and C (apt upgrade of a shared package). ADR-015 amended: Flash listens `443 ssl` without `http2`; `on` is not allowed while dental shares the socket on nginx < 1.25.1; re-enabling needs a new ADR with PO + dental-owner consent.
2. **`sudo systemctl stop|start flash-backend` — CONFIRMED** for the Flash unit only (ADR-017 DB restore on rollback). The TASK-013 constraint list and TASK-014 notes are updated; the full Flash sudo list is now written in ADR-015 ("sudo on the server").
3. **Pre-certificate health — ACCEPTED:** public checks over `http://`, token endpoints checked on 127.0.0.1 only, never over plain HTTP; once the cert exists https + token checks are mandatory (the code switches on the cert's presence). Recorded in ADR-015. **collectstatic duplicate `admin/js/popup_response.js` (jazzmin overriding admin) — ACCEPTED as harmless** (the first finder wins, the jazzmin file is the intended one).
4. Other deviations — ACCEPTED: SQLite online backup with the system `python3` stdlib (ADR-017 wording amended); `setup-server --bootstrap-only`; the validation-only safe-apply test mode (`FLASH_NGINX_ROOT=/tmp/flash-*`, never set by operator scripts).

**Findings:**
1. [non-blocking, fix at the start of TASK-014 before the first live apply] `deploy/scripts/lib/templates.sh` still accepts `NGINX_HTTP2=on`. Per BLK-013 make `on` a hard refusal (exit 2, message naming BLK-013/ADR-015) so the dental constraint cannot be broken by one `.env` line.
2. [non-blocking, fix at the start of TASK-014] `deploy/scripts/deploy.sh:60` checks only `backend/` and `frontend/` for uncommitted changes, but the nginx/unit/shared.env applied live are rendered from the local `deploy/` tree. Include `deploy/` (and the root `Makefile`) in the dirty check and record it in `REVISION`, so live config is always reproducible from a commit.
3. [non-blocking] `certbot certonly --nginx` temporarily edits the Flash site file during the challenge; the dental guard runs around `tls.sh`. If the guard reports any non-Flash change (e.g. `options-ssl-nginx.conf`), stop and report (as already required).
4. [info] `make deploy` needs `backend/` and `frontend/` committed (HEAD has neither) — the orchestrator commits before TASK-014; the backend tasks' TL verdicts are still pending the server validation run.

**Commands run** (local + an isolated nginx test on the server; nothing live applied):
```
bash -n on 22 files (deploy/scripts/*.sh, lib/*.sh)                         → all OK
shellcheck -x (0.11.0, .shellcheckrc: SC2119 only) on all scripts           → clean, EXIT 0
render-templates.sh --out <scratchpad>/render (from the local .env)          → 6 files; no unrendered ${…}; 443 listeners "listen 443 ssl;" (no http2);
                                                                               unit ExecStart access format %%(U)s, no %%(r)s/%%(q)s;
                                                                               shared.env: __GENERATE__ secrets, NUM_PROXIES=1, filecache, API_DOCS_PUBLIC=False,
                                                                               no FLASH_NEW_USER_PASSWORD/DJANGO_ENV_FILE
server, /tmp/flash-tl-nginxtest only (temp self-signed cert, log paths in /tmp, -e /tmp error log):
  sudo nginx -t -c …/nginx-http.conf  (both Flash http bootstrap sites)      → syntax ok, test successful
  sudo nginx -t -c …/nginx-full.conf  (both Flash TLS sites)                 → syntax ok, test successful
  temp dir removed; no flash-* file created in /var/log/nginx; dental-clinic-backend active
code inspection: templates (api/web full + http), backend.service.template, shared.env.template, lib/templates.sh,
  lib/server.sh (_fs_health, safe-apply, TLS, rollback stop/start, seed-qa-users incl. qa_inactive detection), deploy.sh, tls.sh, health-check.sh
```
Not run (by instruction): `make qa-remote`, `make test-backend-remote`, any live apply.

### Bug routing — 2026-09-28 — team-lead

BUG-002 (Low) confirmed and ASSIGNED to **Infrastructure**. Scope: `deploy/nginx/api*.conf.template` only. Decision: keep nginx's server-level `nosniff`, add `proxy_hide_header X-Content-Type-Options;` in the proxied `location /`; Django unchanged. Validation: local render + isolated `nginx -t` in `/tmp/flash-*` on the server; no live apply outside the next `make deploy`. Then READY_FOR_REVIEW → TL review → shipped by TASK-015's roll-forward deploy → QA re-test (TC-001-SEC-03, one value on `/api/status/`, `/static/…`, a 404). The TASK-015 verification of the other TASK-013 criteria is unaffected.

### Review — 2026-09-28 — team-lead — code (BUG-002 fix)

**Verdict:** APPROVED

**Checked:**
- [x] Scope: only `deploy/nginx/api.conf.template` and `deploy/nginx/api.http.conf.template`; Django unchanged; web site untouched
- [x] TLS variant: `proxy_hide_header X-Content-Type-Options;` in the proxied `location /`; the server-level `add_header … nosniff always` is inherited by `/static/`, `/media/` and `/` (none of those locations has its own `add_header`, so inheritance is not broken) → exactly one header everywhere, including nginx-generated errors
- [x] **Deviation ACCEPTED:** the http bootstrap variant also gets a server-level `add_header X-Content-Type-Options "nosniff" always;`. Without it, hiding the upstream copy would have left the pre-TLS variant with **no** header at all. It keeps both variants consistent and only affects the bootstrap phase (and the ACME location, harmlessly)
- [x] No `http2`, no other header or location change (BLK-013/ADR-015 hold)

**Findings:**
1. [non-blocking] The new comment says "the server-level add_header below/above"; tidy the wording in a later change. No functional effect.

**Commands run** (nothing applied live):
```
render-templates.sh --out <scratchpad>/render2                      → OK; api http: add_header nosniff (server) + proxy_hide_header in location /;
                                                                      api full: add_header nosniff (server, line 39) + proxy_hide_header in location /
server, /tmp/flash-tl-nginxtest2 only (temp self-signed cert, logs in /tmp, -e):
  sudo nginx -t -c …/nginx-http.conf                                 → syntax ok, test successful
  sudo nginx -t -c …/nginx-full.conf                                 → syntax ok, test successful
  temp dir removed (0 /tmp/flash-tl-* left)
```
**After the roll-forward deploy (TASK-015):** the rendered API file differs, so `make deploy` safe-applies it (`nginx -t` → reload). Evidence for QA: one `x-content-type-options: nosniff` on `/api/status/`, a `/static/` file and a 404, and `Cache-Control: no-store` on `/api/health/` 401 (BUG-001).

### Review — 2026-09-28 — team-lead — final

**Verdict:** APPROVED — TL final sign-off.
- QA evidence: `.ai/reports/qa/FEAT-004-qa-report.md` (PASS, 13/13 AC), BUG-002 re-test run 20260927-234058-143079; live check: exactly one `X-Content-Type-Options` on `/api/status/`.
- No unreviewed changes: the BUG-002 fix reviewed, committed as `d6669b6`; `git diff d6669b6 HEAD -- deploy Makefile .env.example` empty.
- Docs: `deploy/README.md` complete (FEAT-004 AC12, QA followed it for health/rollback).
- Live state checked read-only by the TL: `make status` → current `20260927-232246` (`d6669b6`, dirty=false), previous `20260927-205208` (from PREVIOUS), flash-backend active, NRestarts 0; `make health` ALL CHECKS PASSED; dental-clinic-backend active, MainPID 18284, NRestarts 0.

## QA Log
- 2026-09-28 | qa | IN PROGRESS | BUG-002 (Low) filed: duplicate X-Content-Type-Options on the API site; live deploy/restart/rollback observation pending (permission)
- 2026-09-28 | qa | PASS | .ai/reports/qa/FEAT-004-qa-report.md; release 20260927-232246 (d6669b6); runs 20260927-233545-139616, -233803-141021, -233920-141829, -233518-139162

## Sign-off
- TL final review: ☑ (team-lead, 2026-09-28)
- QA verdict: ☑ PASS (.ai/reports/qa/FEAT-004-qa-report.md; release 20260927-232246 (d6669b6); runs 20260927-233545-139616, -233803-141021, -233920-141829, -233518-139162)
- PM acceptance: ☑ (project-manager, 2026-09-28; FEAT-004 accepted, .ai/reports/pm/sprint-01-acceptance-2026-09-28.md)
