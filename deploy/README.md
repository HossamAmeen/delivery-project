# Flash — deployment & operations

Owner: Infrastructure (the TL reviews every change). Decisions: ADR-012, 013, 015, 016, 017, 018 in
`.ai/architecture/decisions.md`; design note `.ai/reports/infrastructure/FEAT-004-infra-design.md`.

## Overview

- **One environment:** a shared GCP VPS (`34.123.215.195`) that also runs the live **dental-clinic** app.
  Flash must never modify dental (see *Co-hosting rules*).
- **Mode:** `DEPLOYMENT_MODE=systemd`, the only implemented mode. `docker` or an empty/invalid value makes
  **every** script exit with code 2 (`docker mode is deferred (ADR-015)`). No Docker on the server.
- **Operator-driven** (no CI yet, BLK-012): every command runs from the local machine over SSH via `make` →
  `deploy/scripts/*`. Every script reads the root `.env`, validates it, supports `--dry-run` (`make … DRY_RUN=1`:
  read-only probes still run, and nothing on the server changes), logs with UTC timestamps and masks secret values.
  One Flash operation at a time (local lock `${TMPDIR:-/tmp}/flash-ops.lock`).
- **Tests and QA run on the server, never locally** (REQ-009, ADR-018). The local machine only builds (PWA, shellcheck, renders).

```
deploy/
├── README.md
├── env/shared.env.template            → /srv/flash/shared/.env (only if absent; secrets generated on the server)
├── nginx/api.conf.template            API site, TLS          (+ api.http.conf.template: port-80 bootstrap)
├── nginx/web.conf.template            PWA site, TLS          (+ web.http.conf.template: port-80 bootstrap)
├── systemd/backend.service.template   flash-backend.service (gunicorn 127.0.0.1:${BACKEND_PORT})
└── scripts/
    ├── lib/common.sh         env, mode, logging, redaction, --dry-run, remote_fn ro|rw
    ├── lib/dental_guard.sh   dental preflight + before/after snapshot/compare (read-only)
    ├── lib/templates.sh      envsubst with an explicit variable list
    ├── lib/server.sh         functions executed on the server (_fs_*)
    ├── lib/ops.sh            op lock, nested guard, staging, ops_remote
    ├── setup-server.sh  deploy.sh  deploy-frontend.sh  deploy-backend.sh  migrate.sh  collectstatic.sh
    ├── restart.sh  restart-backend.sh  restart-frontend.sh  health-check.sh  rollback.sh  tls.sh  prune.sh
    ├── seed-qa-users.sh  render-templates.sh  status.sh  remote-test.sh
    └── .shellcheckrc         (cd deploy/scripts && shellcheck -x -P . *.sh lib/*.sh)
```

Server layout (`hossam:hossam` throughout; `make setup-server` creates it and enforces and verifies the modes):
```
/srv/flash/                          0755
├── current -> releases/<id>         atomic switch (ln -sfn tmp && mv -T)
├── releases/                        0755   <YYYYMMDD-HHMMSS>/{backend/, frontend/dist/, venv/, REVISION, MIGRATION_STATE}
├── shared/                          0751   others may traverse (nginx), not list
│   ├── .env                         0600
│   ├── static/  media/              0755   served by nginx (/static/, /media/)
│   ├── db/  backups/  cache/        0700   SQLite DB, pre-migrate/pre-rollback backups, throttle cache
│   └── logs/                        0750
├── sandbox/                         0750   backend test runs (ADR-018)
└── qa/                              0750   QA suite/venv/results, credentials.env (0600), browsers/
~hossam/.local/bin/{uv,uvx}   ~hossam/.local/share/uv/python/   ~hossam/.cache/uv/   ~hossam/.config/uv/uv-receipt.json
```
www-data can read `shared/static` and `shared/media` but cannot list `shared/` or read `db/`, `backups/` or `.env`. `setup-server` checks this every run.

Exit codes: `0` ok · `1` runtime failure · `2` configuration/argument error (env, mode, ref, missing variable) ·
`3` dental guard violation · `255` SSH failure. `remote-test.sh` exits with the test run's own code. `make` turns
any failure into `2`, so call the script directly when you need the exact code.

## Server requirements

Verified in `.ai/reports/infrastructure/server-audit-2026-09-27.md`:
- Ubuntu 24.04, 2 vCPU, 3.8 GB RAM, **no swap**, ≥ `MIN_FREE_DISK_MB` (1500) free on `/srv`.
- SSH user `hossam` with passwordless sudo. sudo is used only for: `install -d` under `/srv/flash`; the unit file
  `/etc/systemd/system/${BACKEND_SYSTEMD_SERVICE}.service` + `daemon-reload|enable|restart|stop|start` of that unit;
  the two Flash nginx site files + links; `nginx -t` and `systemctl reload nginx`; certbot for `${CERT_NAME}`; read-only
  checks (`ss -p`, `certbot certificates|show_account`, `-u www-data test`); Playwright `install-deps` (`--with-e2e` only).
- nginx 1.24, certbot + `certbot.timer`, curl, rsync, envsubst, flock, perl, tar, base64, python3 (all present).
- Python 3.13 comes from **uv** for `hossam` only (ADR-016). Node is **not** used on the server.
- DNS of both Flash names → the server. Port `BACKEND_PORT` (8010) free or held by `flash-backend`.
- Local build machine: bash, git, rsync, ssh, envsubst, node ≥ 20.19 / npm (PWA build).

## SSH setup

- Key-based only: `SSH_KEY_PATH` (default `~/.ssh/id_ed25519`) is referenced by path and never printed or copied.
- Every connection uses `-i $SSH_KEY_PATH -p $SERVER_PORT -o BatchMode=yes` and is multiplexed
  (`ControlPath=${TMPDIR:-/tmp}/flash-ssh-%C`, 60 s).
- Check: `ssh -i ~/.ssh/id_ed25519 -o BatchMode=yes hossam@34.123.215.195 true` and `make status`.

## Environment variables

Two files (ADR-012/015):
1. **Root `.env`** (local, git-ignored, copy of `.env.example`): deployment variables only, **no application
   secrets**. `ENV_FILE=/path` selects another file. A variable already set in the shell overrides the file
   (for example `DEPLOYMENT_MODE=docker make setup-server` to see the mode check).
2. **`/srv/flash/shared/.env`** (server only, 0600): the application variables (the `backend/.env.example` names,
   server values from `deploy/env/shared.env.template`: production settings, SQLite `DATABASE_URL`,
   `RATELIMIT_CACHE_URL=filecache:///srv/flash/shared/cache`, `NUM_PROXIES=1`, `SECURE_PROXY_SSL_HEADER`, hosts/CORS/CSRF,
   `API_DOCS_PUBLIC=False`, HSTS include/preload False). `setup-server` creates it **only if absent** and generates
   `SECRET_KEY` and `HEALTH_CHECK_PASSWORD` on the server; they never leave it. If it exists, missing keys are
   *reported* and must be added by hand; nothing is overwritten. `FLASH_NEW_USER_PASSWORD` and `DJANGO_ENV_FILE`
   never belong in it. To change a value: `ssh … ; nano /srv/flash/shared/.env; make restart TARGET=backend`.

| Variable | Default | Used for |
|---|---|---|
| `APP_NAME` | `flash` | naming |
| `DEPLOYMENT_MODE` | `systemd` | mode (validated by every script) |
| `SERVER_HOST` / `SERVER_USER` / `SERVER_PORT` | `34.123.215.195` / `hossam` / `22` | SSH target |
| `SSH_KEY_PATH` | `~/.ssh/id_ed25519` | SSH key (path only) |
| `DEPLOY_PATH` | `/srv/flash` | server root |
| `API_DOMAIN` / `WEB_DOMAIN` | `api.delivery.hossam-ameen.online` / `delivery.hossam-ameen.online` | nginx, TLS, QA URLs |
| `BACKEND_PORT` | `8010` | gunicorn bind (never 8000) |
| `BACKEND_SYSTEMD_SERVICE` | `flash-backend` | unit name (must start with `flash-`) |
| `GUNICORN_WORKERS` / `_THREADS` / `_TIMEOUT` | `2` / `2` / `30` | unit (TASK-013) |
| `BACKEND_MEMORY_MAX` | `700M` | unit `MemoryMax` |
| `PYTHON_VERSION` | `3.13` | uv-managed interpreter, all venvs |
| `UV_VERSION` | `0.12.19` | pinned uv installer |
| `RELEASES_TO_KEEP` / `DB_BACKUPS_TO_KEEP` | `5` / `5` | retention (TASK-013) |
| `MIN_FREE_DISK_MB` | `1500` | deploy disk check |
| `HEALTH_CHECK_TIMEOUT` | `60` | deploy health wait |
| `AUTO_DEPLOY` / `AUTO_ROLLBACK` | `false` / `true` | deploy behaviour |
| `ROLLBACK_RESTORE_DB` | `auto` | ADR-017 |
| `CERT_NAME` | `flash-delivery` | certbot cert name (not a dental name) |
| `NGINX_HTTP2` | `off` | must be `off` (BLK-013 resolved): `on` is refused with exit 2, because nginx 1.24 would switch dental's shared 443 socket to HTTP/2 too |
| `LETSENCRYPT_EMAIL` | *(empty)* | **optional**: the server already has a registered Let's Encrypt production ACME account, which certbot reuses when this is empty (no `-m`) |
| `VITE_API_BASE_URL` | `https://api.delivery.hossam-ameen.online` | PWA build |
| `DENTAL_GUARD_DOMAINS` | `dental.hossam-ameen.online,api.dental.hossam-ameen.online` | guard HTTPS checks |
| `DENTAL_GUARD_SERVICE` | `dental-clinic-backend` | guard unit checks |
| `DENTAL_GUARD_PORT` | `8000` | guard port checks |
| `DENTAL_GUARD_PATH` | `/srv/dental-clinic` | guard path assertion (never read) |

Runner overrides (environment, optional): `BACKEND_SRC_DIR`, `BACKEND_RESULTS_DIR`, `QA_SRC_DIR`,
`QA_RESULTS_LOCAL_DIR`, `REMOTE_TEST_TIMEOUT` (s per step, default 2700), `REMOTE_TEST_LOCK_WAIT` (s, 1800),
`RESULTS_TO_KEEP` (10), `DENTAL_GUARD_DIR` (snapshot dir, default `${TMPDIR:-/tmp}/flash-dental-guard`).

## Co-hosting rules (dental-clinic)

The server runs the live dental-clinic app: `dental-clinic-backend.service` (gunicorn `127.0.0.1:8000`),
`/srv/dental-clinic`, nginx sites `*.dental.hossam-ameen.online` plus includes under `/etc/nginx/dental-clinic/`,
and the cert `dental.hossam-ameen.online`. **Flash never reads `/srv/dental-clinic`, never touches port
8000 or the dental unit (status queries only), and never edits any non-Flash nginx, systemd or certbot file.**
It also leaves `~hossam/dental-qa` and `~hossam/.npm` alone.

`lib/dental_guard.sh` enforces this around every state-changing Flash operation (`setup-server`, `deploy`, `restart`,
`rollback`, `tls`; nested calls reuse the outer snapshot):
- **Preflight (static):** `BACKEND_PORT ≠ DENTAL_GUARD_PORT` and the port is free or held by the Flash unit;
  `DEPLOY_PATH` and `DENTAL_GUARD_PATH` are not nested; the service name starts with `flash-`; the Flash
  domains and `CERT_NAME` don't contain `dental` and aren't dental domains. A violation exits with code 3.
- **Snapshot before/after (read-only):** sha256 of every file and symlink target under `/etc/nginx/` except
  the two Flash site files; `/etc/letsencrypt/{options-ssl-nginx.conf,ssl-dhparams.pem,renewal/*.conf}` except
  Flash's; the dental unit's is-active, MainPID, start time, NRestarts and unit file hash; the listener count on
  port 8000; the HTTPS status of each dental domain (currently 200 and 302). Any difference fails the command
  loudly (exit 3) and prints the diff. Snapshots are kept in `${TMPDIR:-/tmp}/flash-dental-guard/`.
- The guard hashes all of `/etc/nginx/`, a superset of the ADR-015 list, because dental's includes live
  outside `sites-*` and `conf.d` (audit deviation 1).

Extra co-hosting rules enforced by the tooling:
- nginx: only `sites-available/${API_DOMAIN}`, `sites-available/${WEB_DOMAIN}` and their `sites-enabled` links are ever
  written; safe-apply backups and test configs live under `/tmp/flash-*` (never under `/etc/nginx`); every reload
  follows a passing `nginx -t`; nginx is never restarted. Flash sites never declare `default_server`.
- `http2` stays off on the shared 443 socket (BLK-013).
- certbot: only `certonly --nginx --cert-name ${CERT_NAME}` for the two Flash names, and `renew --dry-run --cert-name ${CERT_NAME}`.
- systemd: only `${BACKEND_SYSTEMD_SERVICE}` (must start with `flash-`).

## Commands

| Command | What it does |
|---|---|
| `make help` | lists every target |
| `make setup-server [BOOTSTRAP_ONLY=1] [WITH_E2E=1]` | layout + modes (verified), uv, Python; then `shared/.env` (if absent), systemd unit (install, daemon-reload, enable; restarted only if a release exists), both nginx sites via safe-apply (port-80 variant until the cert exists). Idempotent |
| `make deploy [ALLOW_DIRTY=1]` | new release, see *Deploy* |
| `make restart TARGET=backend\|frontend\|all` | backend: `systemctl restart` + local health wait · frontend: re-render web site + safe-apply + reload |
| `make migrate` | plan → SQLite backup → migrate for `current` |
| `make collectstatic` | collectstatic for `current` |
| `make health [TIMEOUT=60]` | health checks (read-only), retried until TIMEOUT |
| `make rollback [TO=<id>] [RESTORE_DB=auto\|always\|never]` | see *Rollback* |
| `make tls` | certificate for the two Flash names + switch to TLS templates + renew dry-run |
| `make prune` | retention |
| `make seed-qa-users` | QA users with server-generated passwords → `/srv/flash/qa/credentials.env` |
| `make status` · `make logs [LINES=200] [FOLLOW=1]` | unit/releases/backups/nginx/cert overview · `journalctl -u flash-backend` |
| `make render [OUT=dir]` | render all templates locally for inspection |
| `make test-backend-remote …` · `make qa-remote …` · `make throttle-reset` | see *Remote testing* |

Every target accepts `DRY_RUN=1`. First-time bring-up (TASK-014): `make setup-server` → `make deploy` → `make tls` →
`make health` → `make seed-qa-users` → `make qa-remote ARGS='-m smoke'`.

## systemd mode

`/etc/systemd/system/flash-backend.service` (from `deploy/systemd/backend.service.template`):
`User/Group=hossam`, `WorkingDirectory=/srv/flash/current/backend`, `EnvironmentFile=/srv/flash/shared/.env`,
`ExecStart=/srv/flash/current/venv/bin/gunicorn config.wsgi:application --bind 127.0.0.1:8010 --workers 2 --threads 2
--timeout 30 --max-requests 1000 --max-requests-jitter 100 --access-logfile - --access-logformat
"%%({x-forwarded-for}i)s %%(t)s \"%%(m)s %%(U)s %%(H)s\" %%(s)s %%(b)s %%(D)sus \"%%(a)s\"" --error-logfile -`.
The access log holds the **path only** (`%(U)s`), never `%(r)s` or `%(q)s`, so a `?password=` never reaches journald.
Each `%` is doubled for systemd; the parsed argv was verified. `Restart=always`, `RestartSec=5`, `UMask=0022`,
`MemoryMax=700M`, `TasksMax=128`, `NoNewPrivileges`, `PrivateTmp`, `ProtectSystem=full`, `ProtectHome=read-only`,
`ReadWritePaths=/srv/flash/shared`, `WantedBy=multi-user.target` (starts at boot). Logs: `make logs`.

## nginx and TLS

- Exactly two files, `/etc/nginx/sites-{available,enabled}/api.delivery.hossam-ameen.online` and
  `…/delivery.hossam-ameen.online`, rendered with `envsubst` and an explicit list (nginx `$host`, `$uri`, … survive).
- **API:** `/static/` and `/media/` are `alias`es to `shared/`. Everything else goes to `proxy_pass http://127.0.0.1:8010` with
  `Host $host`, `X-Forwarded-For $remote_addr` (**overwrite**; `NUM_PROXIES=1`), `X-Forwarded-Proto $scheme` and
  `client_max_body_size 10m`. `log_format flash_api` logs `$uri` only (no query strings) to `/var/log/nginx/flash-api.*.log`.
- **Web:** `root /srv/flash/current/frontend/dist`, `try_files $uri $uri/ /index.html`. `index.html`, `sw.js` and
  `manifest.webmanifest` get `no-cache`; `/assets/` gets 1-year `immutable`. Logs go to `/var/log/nginx/flash-web.*.log`.
- **Both:** port 80 serves `/.well-known/acme-challenge/` and a 301 to https. On 443: `ssl`, the certificate
  `/etc/letsencrypt/live/flash-delivery/`, and HSTS `max-age=31536000` without includeSubDomains/preload (the parent domain is
  shared with dental). No `http2` (`NGINX_HTTP2=on` is refused, BLK-013).
- **Phases:** until the certificate exists, `setup-server`/`deploy` install the `*.http.conf` variants (port 80 only).
  `make tls` issues the certificate and switches to the TLS variants.
- **Safe-apply** (every nginx change): back up the Flash files to `/tmp/flash-nginx-backup-*` → write → `sudo nginx -t` →
  on failure restore the previous files (or remove the new ones), run `nginx -t` again, exit 1 **without reloading** → on
  success `sudo systemctl reload nginx`. It refuses any other file name, and an unchanged file means no reload.
- **TLS:** `sudo certbot certonly --nginx --cert-name flash-delivery -d api.delivery… -d delivery… --non-interactive
  --agree-tos [-m $LETSENCRYPT_EMAIL] --deploy-hook "nginx -t && systemctl reload nginx"`. With `LETSENCRYPT_EMAIL`
  empty, the registered production ACME account is reused (the script fails early if `certbot show_account` finds none).
  Issuance is skipped if the certificate already covers both names. Renewal comes from the existing `certbot.timer`; it
  is verified with `certbot renew --dry-run --cert-name flash-delivery` (never a bare `certbot renew`).

## Deploy

`make deploy` (`deploy/scripts/deploy.sh`):
1. **Preflight:** env + mode; `backend/`, `frontend/`, `deploy/` and the root `Makefile` committed (else refused, unless
   `ALLOW_DIRTY=1`: recorded as `dirty=true`, `dirty_paths=…`, `dirty_checked=…` in `REVISION`; never for the release of record); HEAD contains `backend/requirements/production.txt`; SSH; disk ≥ `MIN_FREE_DISK_MB`;
   dental snapshot + port guard.
2. **Build locally:** `cd frontend && npm ci && VITE_API_BASE_URL=… npm run build` (dist must contain `id="app"`).
3. **Stage:** `git archive HEAD backend` + `frontend/dist` + `REVISION` (release, sha, dirty, time, builder).
4. **Upload:** `rsync -a --delete --link-dest=<previous release>` → `releases/<UTC YYYYMMDD-HHMMSS>` (dirs 0755, files 0644).
5. **Server build:** uv venv (Python 3.13) + `uv pip install -r backend/requirements/production.txt`; `check --deploy`
   (warnings logged; W004/W008 are expected because nginx handles HSTS and the redirect); `collectstatic --noinput`.
6. **Migrate** (old release still serving): plan → SQLite online backup → `migrate --noinput` → `MIGRATION_STATE`.
7. **Switch** `current` atomically → `systemctl restart flash-backend` → local health wait.
8. **nginx safe-apply** only if the rendered files changed.
9. **Health** until `HEALTH_CHECK_TIMEOUT`. **Dental compare.** **Prune.** Summary: release, sha, previous, duration, health.

Failure **before** the switch: `releases/<id>` is removed and the live site is untouched (exit 1). Failure **after**
the switch: with `AUTO_ROLLBACK=true` it rolls back to the previous release and prints the outcome (exit 1). On a first deploy there is nothing to roll back to.
Migrations must be backward compatible with the previous release (expand → deploy → contract, ADR-013).

## Health

`make health` (read-only, on the server):
- `systemctl is-active flash-backend`
- `GET http://127.0.0.1:8010/api/health/` (`"healthy"`) and `/api/health/ready/` (`"ready"`)
- the same through `https://api.delivery…`, plus `https://api.delivery…/api/status/` (`"ok"`)
- `https://delivery…/` returns 200 and contains `id="app"`
- `sudo nginx -t`

The token is read from `shared/.env` on the server and passed as the `X-Health-Check-Token` header through
`curl -H @-` (stdin). It never appears in argv, output or logs, and `?password=` is never used. Before the certificate exists, the public checks use
http and **skip** the token endpoints. Every failing check is named (`FAIL  …`), and the exit code is 1.

## Rollback

`make rollback [TO=<id>] [RESTORE_DB=auto|always|never]` (default `ROLLBACK_RESTORE_DB=auto`):
1. Target = the release before `current`, or `TO`. It fails clearly when there is none.
2. DB decision (SQLite, ADR-017): `auto` restores only if the release being rolled back **applied migrations**
   (`MIGRATION_STATE` `applied=yes`); `always` restores its pre-migrate backup; `never` doesn't. If no backup exists
   (first deploy), the DB is not restored and a warning says so.
3. `current` → target. With a restore: stop the unit → save the live DB as `shared/backups/pre-rollback-<ts>.sqlite3` →
   copy the backup in (the WAL/SHM files are removed) → start. **Every write made after that deploy is lost** (the script warns).
   Without a restore: restart.
4. Health (`HEALTH_CHECK_TIMEOUT`) → dental compare.

Reverse migrations are never run. `DRY_RUN=1` prints the exact decision without changing anything.

## Resource limits and retention

- gunicorn 2 workers × 2 threads, `MemoryMax=700M`, `TasksMax=128`; no builds on the server; one pytest worker in the runners.
- `RELEASES_TO_KEEP=5` (the current release and its previous are always kept). `DB_BACKUPS_TO_KEEP=5` per kind
  (`flash-*`, `pre-rollback-*`), and the current release's rollback backup is always kept.
- Deploy refuses to start below `MIN_FREE_DISK_MB`. Each release is ~20 MB thanks to hardlinks (`--link-dest` + the uv cache).
- Remote-test results: the last 10 runs (server and local).

## Remote testing (ADR-018)

Other agents only need these commands. Each run ships the sources over SSH (a tar stream), takes a
server-side lock (one run per suite at a time; a second run waits), uses a uv venv on Python 3.13 that is
rebuilt **only when the requirements files change**, streams the output back, copies the results locally,
and exits with the test exit code. No test ever runs locally. Parallel pytest (`-n`, xdist) is refused, and
leftover processes are killed after the run.

### Backend — `make test-backend-remote`
```bash
make test-backend-remote WORKTREE=1                        # working tree of backend/, including uncommitted changes
make test-backend-remote REF=<commit|branch|tag>           # git archive of that ref (default: HEAD)
make test-backend-remote WORKTREE=1 STEPS=pytest ARGS='apps/users -k login'
make test-backend-remote WORKTREE=1 STEPS=lint             # ruff check + ruff format --check only
deploy/scripts/remote-test.sh backend --worktree -- -x     # direct call (exact exit code)
```
- **Steps** (default all, `STEPS=` takes a comma list): `ruff-check` (`ruff check .`), `ruff-format`
  (`ruff format --check .`), `check` (`manage.py check`), `makemigrations` (`makemigrations --check
  --dry-run`), `pytest` (`--cov --cov-report=term-missing --cov-report=xml --cov-fail-under=80 --junitxml`,
  then `ARGS`). Every selected step runs. The exit code is pytest's if pytest failed, otherwise the first
  failing step's.
- **Environment:** a clean environment (only HOME/USER/LOGNAME/SHELL/TERM survive) plus
  `DJANGO_SETTINGS_MODULE=config.settings.development`,
  `DATABASE_URL=sqlite:////srv/flash/sandbox/test.sqlite3`, `RATELIMIT_CACHE_URL=locmem://`,
  `CELERY_ENABLED=False`, and random throw-away `SECRET_KEY` / `HEALTH_CHECK_PASSWORD`. `shared/.env` is
  never read. `backend/pytest.ini` may override the settings module with `--ds` (it uses `config.settings.test`).
- **Shipped:** `backend/` minus `.env`, `*.sqlite3`, venvs, caches, `.remote-results`, coverage files.
- **Results:** `backend/.remote-results/<run-id>/{output.log,summary.txt,junit.xml,coverage.xml}` and
  `backend/.remote-results/latest` (git-ignored; the last 10 runs are kept locally and on the server).

### QA — `make qa-remote`
```bash
make qa-remote ARGS='--collect-only -q'
make qa-remote ARGS='-m smoke'
make throttle-reset && make qa-remote ARGS='-m ratelimit' && make throttle-reset
```
- Ships `qa/` to `/srv/flash/qa/suite` and runs `pytest ARGS` on the server (`--junitxml` added unless
  given) against the **public HTTPS URLs**.
- Environment exported **only into the pytest process:** `QA_BASE_URL=https://${API_DOMAIN}`,
  `QA_WEB_URL=https://${WEB_DOMAIN}`, `QA_RESULTS_DIR` (write artifacts there), `QA_DENTAL_DOMAINS`,
  `PLAYWRIGHT_BROWSERS_PATH=/srv/flash/qa/browsers`, `QA_HEALTH_TOKEN` (read server-side from
  `shared/.env` `HEALTH_CHECK_PASSWORD`, if present) and every `QA_*` line of `/srv/flash/qa/credentials.env`
  (from `make seed-qa-users`, TASK-013).
- **Redaction:** the token and every `QA_*PASSWORD*` value are masked as `***` in the streamed output,
  `output.log`, and every text artifact (xml/log/txt/json/html). Truncated prefixes such as pytest's
  `'abcdef...'` are masked too. Binary artifacts (Playwright traces) are not scrubbed, so don't put secrets
  into browser flows.
- **Results:** `qa/.results/<run-id>/` + `qa/.results/latest` (junit.xml, output.log, summary.txt, anything
  written to `QA_RESULTS_DIR`, `suite/.results/`, and Playwright `test-results/` as `playwright/`).
- Playwright browsers are not installed yet (TASK-013 `setup-server --with-e2e`).

### Throttle reset — `make throttle-reset`
Empties `/srv/flash/shared/cache/` (the FileBasedCache throttle counters, ADR-017) and prints the number of
removed files. It never touches the database. `DRY_RUN=1` only counts the files.

## Troubleshooting

- **`nginx -t` fails during setup/deploy/tls/restart:** safe-apply already restored the previous Flash files and did
  **not** reload, so the live nginx is unchanged. Read the `[nginx -t]` lines, fix the template, then
  `make render OUT=/tmp/flash-render` and inspect. Never edit the files under `/etc/nginx` by hand.
- **Health fails after a deploy:** with `AUTO_ROLLBACK=true` the previous release is already back. Look at `make logs
  LINES=300`, `make status`, `make health` (each FAIL line names the check). `health token` FAIL means
  `HEALTH_CHECK_PASSWORD` is missing from `shared/.env`. A 400 on the public checks usually means `ALLOWED_HOSTS`;
  a 503 on ready lists the failing check name.
- **Disk full / below `MIN_FREE_DISK_MB`:** `make status` (disk line), then `make prune`. Old venvs live in
  `releases/*`, and `~/.cache/uv` can be cleaned with `~/.local/bin/uv cache prune`. Remote-test results are capped at 10 runs.
- **"database is locked" (SQLite):** WAL + `busy_timeout=20000` + `IMMEDIATE` should prevent it. Check for a stuck process
  (`make logs`), then `make restart TARGET=backend`. Never copy the DB file while the unit runs; use the backup API
  (`migrate.sh` does). A manual restore is `make rollback RESTORE_DB=always` or: stop the unit, copy the backup over
  `shared/db/flash.sqlite3`, delete `-wal`/`-shm`, start.
- **Dental guard exit 3:** something in the dental footprint changed during the operation. Stop and compare the two
  snapshot files printed in the log, and do not retry until it is explained.
- **`another Flash operation holds …flash-ops.lock`:** another deploy/restart is running from this machine; wait for it.
