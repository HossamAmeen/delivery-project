# TASK-013 — validation evidence (2026-09-27)

Target server `hossam@34.123.215.195`. **No live nginx, systemd or certbot change was made.** After all the work:
`ls /etc/systemd/system | grep -c flash` → 0, `ls /etc/nginx/sites-available | grep -c delivery` → 0, no `/srv/flash/shared/.env`.
The only live change is the TL-mandated permission scheme under `/srv/flash` (`setup-server --bootstrap-only`).
Every test artifact lived under `/tmp/flash-*` on the server or in the agent scratchpad, and was removed afterwards.

## 1. Static checks
- `cd deploy/scripts && bash -n` on all 22 files (18 scripts + 5 libs, including TASK-012's) → OK.
- `shellcheck -x -P . *.sh lib/*.sh` (0.11.0, scratch venv) → **clean**. `deploy/scripts/.shellcheckrc` disables SC2119
  only (optional-argument helpers). Remaining inline directives have justifications in comments.
- Secret grep over `deploy/`, `Makefile`, `.env.example` (`(SECRET_KEY|PASSWORD|TOKEN)…=<8+ chars>`, private-key headers)
  → nothing. `shared.env.template` holds only `__GENERATE__` placeholders.

## 2. Mode validation — every script
`DEPLOYMENT_MODE=docker|<empty>|bogus` × 17 scripts (setup-server, deploy, deploy-backend, deploy-frontend,
restart, restart-backend, restart-frontend, migrate, collectstatic, health-check, rollback, tls, prune, seed-qa-users,
render-templates, status, remote-test) → **51/51 exit 2**, e.g. `DEPLOYMENT_MODE=docker: docker mode is deferred (ADR-015)`.
The first run caught deploy.sh without its exec bit (exit 126); fixed.

## 3. Templates (local render with the real `.env.example` values)
`ENV_FILE=.env.example deploy/scripts/render-templates.sh --out …` → 6 files (nginx http+full for both domains,
`flash-backend.service`, `shared.env`). nginx variables survive (`$host`, `$uri`, `$remote_addr`, … present), and
an unresolved `${VAR}` fails the render (exit 2).
- `shared.env` keys vs `backend/.env.example` names: identical except the two excluded on purpose
  (`DJANGO_ENV_FILE`, `FLASH_NEW_USER_PASSWORD`). `NUM_PROXIES=1`,
  `DATABASE_URL=sqlite:////srv/flash/shared/db/flash.sqlite3`, `RATELIMIT_CACHE_URL=filecache:///srv/flash/shared/cache`,
  HSTS include/preload `False`, `SECRET_KEY`/`HEALTH_CHECK_PASSWORD=__GENERATE__`.
- **systemd `ExecStart` argv, parsed by systemd** (the **local** user manager, with an argv-dump stand-in binary;
  a temporary unit in `$XDG_RUNTIME_DIR`, removed afterwards):
  `["config.wsgi:application","--bind","127.0.0.1:8010","--workers","2","--threads","2","--timeout","30","--max-requests","1000","--max-requests-jitter","100","--access-logfile","-","--access-logformat","%({x-forwarded-for}i)s %(t)s \"%(m)s %(U)s %(H)s\" %(s)s %(b)s %(D)sus \"%(a)s\"","--error-logfile","-"]`
  → path-only `%(U)s`, no `%(r)s`/`%(q)s`, and `%%` resolves to `%`.
- `systemd-analyze verify` on the server (`/tmp/flash-unit-test/flash-backend.service`, systemd 255): the single message
  is `Command /srv/flash/current/venv/bin/gunicorn is not executable: No such file or directory` (expected: no release
  yet). **0 specifier messages.**

## 4. nginx `nginx -t` without touching the live config
Temp dir `/tmp/flash-nginx-test`, a temporary self-signed cert in place of `/etc/letsencrypt/live/flash-delivery/`,
log paths redirected into the temp dir (no file created in `/var/log/nginx`):
- isolated **http** variant: `sudo nginx -t -c /tmp/flash-nginx-test/isolated-http.conf` → syntax ok / successful
- isolated **full** variant: `sudo nginx -t -c …/isolated-full.conf` → syntax ok / successful
- **combined** (a copy of the live `nginx.conf` + live `sites-enabled/*` + Flash TLS files):
  - with `http2`: successful **with warnings** `protocol options redefined for 0.0.0.0:443` / `[::]:443`. nginx 1.24
    merges `http2` socket-wide, so Flash would switch dental to HTTP/2 → **BLK-013**, `NGINX_HTTP2=off` default
  - with `NGINX_HTTP2=off`: syntax ok / successful, **no warnings**

## 5. nginx safe-apply (real function, test mode on the server)
`FLASH_NGINX_ROOT=/tmp/flash-safeapply-test` + `FLASH_NGINX_CONF` (writes and `nginx -t -c` redirected; reload skipped):
| Case | Result |
|---|---|
| 1 new files, valid | backup dir → install (root 0644) + links → `nginx -t` ok → "TEST MODE — reload skipped", rc 0 |
| 2 same files again | "Flash site files unchanged — no reload", rc 0 |
| 3 broken API file | `[emerg] unknown directive "this_is_not_a_directive"` → "restoring the previous Flash files, NOT reloading" → `nginx -t after restore` ok → rc 1; hashes afterwards == case 1 (`06ff7e3e…`, `bfa945ef…`) |
| 4 stage contains `dental.hossam-ameen.online.conf` | "refusing nginx file …", rc 2, nothing written |
| 5 broken file on an empty root (first install) | installed → `nginx -t` fails → new files **removed** → rc 1, root empty again |
This test found a real bug, now fixed: stage names (`new_run_id` = second + PID) collided when two uploads ran in the same second.
A random suffix was added.

## 6. Permission scheme (TL decision) — applied for real, `/srv/flash` only
`make setup-server BOOTSTRAP_ONLY=1 DRY_RUN=1` showed the old problem (`BAD www-data test -r shared/static/.: denied`).
The real run gave `fixed shared 750→751, db/backups/cache 755→700, logs 755→750, sandbox/qa 755→750`, then verification:
```
ok hossam:hossam:751 /srv/flash/shared     ok hossam:hossam:755 shared/static, shared/media
ok hossam:hossam:700 shared/db, shared/backups, shared/cache    ok 750 shared/logs, sandbox, qa
ok www-data test -r shared/static/.: ok     ok www-data test -r shared/media/.: ok
ok www-data ls shared: denied               ok www-data test -r shared/db/.: denied
ok www-data test -r shared/backups/.: denied  ok www-data cat shared/.env: denied
```
The re-run had 0 `fixed/created/BAD` lines (idempotent), dental IDENTICAL. The TASK-012 runners still work afterwards: backend
probe 3 passed / exit 0, real `qa/` collect 134/139 exit 0, throttle-reset OK.

## 7. shared/.env logic (real functions, target `/tmp/flash-envtest/.env`)
Plan → `would-create`. 1st install → `created (0600; generated on the server: SECRET_KEY HEALTH_CHECK_PASSWORD)`,
49 keys, 0 placeholders left, both secrets 64 chars (values never printed). 2nd install → `exists (not overwritten)`,
sha unchanged. After deleting 2 keys → `MISSING KEYS …: API_PAGE_SIZE NUM_PROXIES — add them by hand`, nothing added.

## 8. Release pipeline integration test (real `backend/`, `DEPLOY_PATH=/tmp/flash-rbtest`, no systemd/nginx)
- `shared/.env` rendered for the test root. Release A: deploy.sh's rsync command → `deploy-backend.sh` (uv venv
  **Python 3.13.15**, production requirements, `check --deploy`: only W004/W008 (nginx handles HSTS and the redirect), collectstatic 244 files)
  → `migrate.sh`: full plan printed, `no database yet (first deploy): no backup`, `MIGRATION_STATE backup=none applied=yes`
  → switch `current: none -> A`.
- Rollback plan with a single release → `no previous release before A — cannot roll back` (rc 2).
- Release B with `--link-dest A` (79 files hardlinked; B = 21 MB vs A = 74 MB) → migrate: `No planned migration
  operations`, `pre-migrate backup: …/flash-B-<ts>.sqlite3 (132K)`, `applied=no` → switch `A -> B`.
- Rollback plans from B: `auto` → restore DB: no · `always` → restore DB: yes, from `…flash-B-….sqlite3` · `never` → no.
- Standalone `migrate.sh` on current → backup + second `MIGRATION_STATE` record appended.
- `prune.sh` with `RELEASES_TO_KEEP=2 DB_BACKUPS_TO_KEEP=1` → both releases kept (current + previous). After a fix, only the
  current release's rollback backup (its first) is protected beyond the kept count.
- **Not exercised here:** a live rollback switch with unit stop/start, and the live health path. Both belong to TASK-014.

## 9. Dry-runs (systemd mode) — `make <target> DRY_RUN=1`
| Target | Result |
|---|---|
| `setup-server` | exit 0. Plan: `would-create` shared/.env, unit, both nginx sites (http variant); apply steps printed `[dry-run]`; perms verify; dental IDENTICAL |
| `setup-server WITH_E2E=1` | exit 0, `_fs_e2e_install` printed `[dry-run]` |
| `deploy ALLOW_DIRTY=1` | exit 0: full ADR-015 order printed (preflight + dental, frontend build, stage 79 backend files, prepare dir, rsync `--link-dest`, venv/check/collectstatic, migrate, switch, restart + local health, nginx safe-apply, full health, dental IDENTICAL, prune) → "DRY-RUN complete: nothing was changed" |
| `deploy` (clean check) | exit 2: HEAD has no backend (not committed yet) |
| `restart TARGET=all` | exit 0 |
| `health`, `prune`, `seed-qa-users`, `logs` | exit 0 (plan printed) |
| `status` | exit 0 (after a fix: an empty certbot grep had failed it) |
| `migrate`, `collectstatic`, `rollback` | exit 2/1 by design: "no current release on the server (deploy first)" / "no current release — nothing to roll back" |
| `tls` | stops at the precondition: "the Flash nginx sites are not enabled (run 'make setup-server' first)" |

## 10. Frontend build contract (local, scratch copy of `frontend/` without node_modules/dist)
`FRONTEND_SRC_DIR=<scratch> deploy-frontend.sh --out <stage>` → `npm ci` + `VITE_API_BASE_URL=https://api.delivery.hossam-ameen.online npm run build`
(vue-tsc + vite + PWA, 17 s) → exit 0, `dist` staged: 28 files, 476K. `index.html` contains `id="app"`, and the API URL is
present in `assets/index-*.js`.

## 11. Dental
Task-level snapshot before (18:15:36Z) vs after (18:26:14Z): **IDENTICAL (33 entries)**. Every guarded dry-run and real
run also reported IDENTICAL.
