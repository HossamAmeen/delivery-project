# FEAT-004 — infrastructure design note (TASK-013)

Spec: ADR-013/015/016/017/018. This note maps the ADRs onto files and flows. Only `DEPLOYMENT_MODE=systemd`
exists, and `docker` exits with code 2 in every script.

## Script responsibilities
| Script (Make target) | Does | Server state it may change |
|---|---|---|
| `lib/common.sh` | `.env` parsing, mode/var validation, UTC logs, redaction, `run`, `remote_fn ro\|rw` (rw = skipped under `--dry-run`) | — |
| `lib/dental_guard.sh` | preflight + before/after snapshot of dental (read-only), exit 3 on any change | — |
| `lib/templates.sh`, `render-templates.sh` (`render`) | `envsubst` with an explicit list; unresolved `${VAR}` → exit 2 | — (local) |
| `lib/server.sh` | every `_fs_*` server function (shipped by `declare -f`) | see the rows below |
| `lib/ops.sh` | `ops_init`, `ops_remote`, local op lock, nested dental guard, staging uploads (`/tmp/flash-stage-*`) | `/tmp/flash-stage-*` |
| `setup-server.sh` (`setup-server`) | layout + modes (verified incl. www-data checks) → uv → Python → `shared/.env` if absent → unit + daemon-reload + enable → nginx safe-apply (http or TLS variant) → `--with-e2e` | `/srv/flash`, `/etc/systemd/system/flash-backend.service`, the 2 Flash nginx files + links, `qa/browsers`, apt (only with e2e) |
| `deploy.sh` (`deploy`) | full ADR-015 order (below) | a new `releases/<id>`, `current`, DB (migrate), unit restart, nginx (if changed) |
| `deploy-frontend.sh` | local `npm ci && npm run build` → stage `frontend/dist` | — (local) |
| `deploy-backend.sh` | uv venv + production requirements, `check --deploy`, collectstatic | `releases/<id>/venv`, `shared/static` |
| `migrate.sh` (`migrate`) | `--plan` → SQLite online backup → `migrate --noinput` → `MIGRATION_STATE` → prune backups | DB, `shared/backups` |
| `collectstatic.sh` (`collectstatic`) | collectstatic for a release | `shared/static` |
| `restart.sh` / `restart-backend.sh` / `restart-frontend.sh` (`restart TARGET=`) | unit restart + local health · web safe-apply + forced reload | unit, nginx reload |
| `health-check.sh` (`health`) | ADR-015 checks, retries until `HEALTH_CHECK_TIMEOUT` | — (read-only) |
| `rollback.sh` (`rollback`) | switch `current` → optional DB restore (ADR-017) → restart → health → dental compare | `current`, DB, unit |
| `tls.sh` (`tls`) | certbot certonly (skipped if covered) → TLS variant via safe-apply → renew `--dry-run` | certbot `flash-delivery`, the 2 nginx files |
| `prune.sh` (`prune`) | releases (keep N + current + previous), backups (keep N + the current release's rollback backup) | `releases/`, `shared/backups` |
| `seed-qa-users.sh` (`seed-qa-users`) | server-generated passwords → `create_role_user --password-stdin --update` → `qa/credentials.env` 0600 | users table, credentials file |
| `status.sh` (`status`, `logs`) | read-only views | — |
| `remote-test.sh` (TASK-012) | backend / qa / throttle-reset runners | sandbox, qa, `shared/cache` |

## Variables
Root `.env` (deployment, no secrets): `APP_NAME DEPLOYMENT_MODE SERVER_HOST SERVER_USER SERVER_PORT SSH_KEY_PATH
DEPLOY_PATH API_DOMAIN WEB_DOMAIN BACKEND_PORT BACKEND_SYSTEMD_SERVICE GUNICORN_WORKERS GUNICORN_THREADS
GUNICORN_TIMEOUT BACKEND_MEMORY_MAX PYTHON_VERSION UV_VERSION RELEASES_TO_KEEP DB_BACKUPS_TO_KEEP MIN_FREE_DISK_MB
HEALTH_CHECK_TIMEOUT AUTO_DEPLOY AUTO_ROLLBACK ROLLBACK_RESTORE_DB CERT_NAME LETSENCRYPT_EMAIL NGINX_HTTP2
VITE_API_BASE_URL DENTAL_GUARD_*`. The template list is `APP_NAME API_DOMAIN WEB_DOMAIN DEPLOY_PATH BACKEND_PORT
CERT_NAME SERVER_USER GUNICORN_* BACKEND_MEMORY_MAX BACKEND_SYSTEMD_SERVICE NGINX_LISTEN_HTTP2` (the last is derived from `NGINX_HTTP2`).
Server `shared/.env`: the `backend/.env.example` names except `FLASH_NEW_USER_PASSWORD` and `DJANGO_ENV_FILE`.

## nginx safe-apply
```
stage (/tmp/flash-stage-*) ──► names ∈ {API_DOMAIN, WEB_DOMAIN}? ── no ──► exit 2 (nothing written)
        │ yes
        ▼
 changed vs /etc/nginx/sites-available/<d> or link? ── no ──► "unchanged" (reload only if forced, after nginx -t)
        │ yes
        ▼
 backup old files+links → /tmp/flash-nginx-backup-*      (never under /etc/nginx: the dental guard hashes it)
 sudo install -m0644 → sites-available/<d>; ln -sfn → sites-enabled/<d>
 sudo nginx -t ── fail ──► restore backup (or remove new files) → nginx -t again → return 1, NO reload
        │ ok
        ▼
 sudo systemctl reload nginx          (never restart, never nginx -s reload)
```

## deploy / rollback
```
preflight: env+mode · clean backend/+frontend/ (or --allow-dirty) · ssh · disk ≥ MIN_FREE_DISK_MB · dental snapshot + port guard · op lock
 → local PWA build → stage git-archive backend + dist + REVISION → mkdir releases/<id> → rsync --link-dest previous
 → venv + production reqs → check --deploy → collectstatic → [DB backup → migrate → MIGRATION_STATE]
 ── any failure so far: remove releases/<id>, live site untouched, exit 1
 → switch current (ln -sfn tmp && mv -T) → restart unit + local health → nginx safe-apply if changed → full health (retry ≤ HEALTH_CHECK_TIMEOUT)
 ── any failure after the switch: AUTO_ROLLBACK=true → rollback.sh --to <previous>; exit 1 (outcome printed)
 → dental compare → prune → summary

rollback: target = previous (or --to) · restore DB? (--restore-db / --no-restore-db / ROLLBACK_RESTORE_DB auto=only if the
  rolled-back release applied migrations) → switch current → [stop unit → save current DB as pre-rollback-<ts> → copy the
  release's first pre-migrate backup → start] or restart → health → dental compare. Reverse migrations are never run.
```

## Decisions and deviations for TL review
1. `NGINX_HTTP2` defaults to **off** (**BLK-013**): in nginx 1.24, `listen … http2` is socket-wide and would switch dental to HTTP/2.
2. Before the certificate exists, health uses `http://` for the public checks and **skips the token checks** (the token is never sent over plain HTTP).
3. The rollback DB restore uses `systemctl stop`/`start` of the Flash unit. That comes from ADR-017's wording ("stop … start") but isn't in TASK-013's sudo list (`daemon-reload|enable|restart|kill`).
4. The SQLite backup and restore copy use the system `python3` (3.12, stdlib `sqlite3`) on the server rather than the release venv; the online-backup API is the same.
5. `nginx safe-apply` has a validation-only test mode (`FLASH_NGINX_ROOT=/tmp/flash-*` + `FLASH_NGINX_CONF`, no reload). No operator script sets it.
6. `setup-server.sh --bootstrap-only` applies the layout, modes, uv and Python only. It was used in TASK-013 to apply the new permission scheme without any nginx or systemd change.
