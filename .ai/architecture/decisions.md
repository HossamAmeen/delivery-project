# Architecture Decision Records

Owner: Team Lead. Statuses: `PROPOSED` · `ACCEPTED` · `SUPERSEDED by ADR-NNN` · `REJECTED`.
Major changes need a new ADR, as defined in `agents/team-lead.md` §2. Major business changes also need PM/PO approval.

---

## ADR-001 — Backend follows `docs/standards/DRF_SKILL.md`
- **Status:** ACCEPTED (2026-09-27)
- **Context:** The user supplied `docs/standards/DRF_SKILL.md` as the backend engineering standard.
- **Decision:** The backend is built in CREATE mode per `docs/standards/DRF_SKILL.md`: structure, split settings, env configuration, common package, JWT, drf-spectacular, Jazzmin, Health API, DRF throttling, pytest ≥ 80% coverage, Docker local/staging/production, deploy templates, and a Makefile. Its §57 validation commands and §58 DoD are part of every backend task's DoD.
- **Consequences:** Deviations need an ADR. The skill is generic, so Flash-specific rules (ADR-005, ADR-006) sit on top of it. The skill's deployment file *locations* are adapted by ADR-012.
- **Runtime pin (2026-09-27, TASK-001 review):** Django **5.2 LTS** (pinned `5.2.17`; ≥ 5.1 is required by ADR-017's SQLite options; 6.x not adopted until Jazzmin/simplejwt support is proven). Upgrades within 5.2.x are routine; a major upgrade needs a TL decision.
- **Test settings (2026-09-27):** the suite runs with `config.settings.test` (development + isolated LocMem cache, MD5 hasher, test-only app `tests.testapp`), selected by `--ds` in `backend/pytest.ini`.

## ADR-002 — Monorepo layout
- **Status:** ACCEPTED (2026-09-27)
- **Decision:** A single repository with `backend/`, `frontend/`, `mobile/`, `qa/`, `.ai/`, `docs/business/`. Directory ownership is defined in `.ai/README.md`.
- **Consequences:** Agents have clear, non-overlapping write scopes. One version history covers business docs, contracts and code.

## ADR-003 — Custom User model with role, from the first migration
- **Status:** ACCEPTED (2026-09-27)
- **Context:** Django cannot cleanly swap `AUTH_USER_MODEL` after the first migrations. Flash has 4 roles.
- **Decision:** `users.User(AbstractUser)` plus `role` (CUSTOMER, DRIVER, STORE, ADMIN), created in the foundation sprint before any `migrate`. Profile models are added per feature. The login identifier (`USERNAME_FIELD`) follows BLK-001. Changing it before production is a simple migration.
- **Consequences:** TASK-003 must land before any other app creates FKs to the user.

## ADR-004 — Business-logic sources of truth
- **Status:** ACCEPTED (2026-09-27)
- **Context:** `docs/business/README.md` declares itself the single source of truth. The agent system requires `.ai/business/business-logic.md`.
- **Decision:**
  - `docs/business/` is **canonical**.
  - `.ai/business/business-logic.md` is the agent-facing digest. It cites the source for every rule and marks gaps as UNDEFINED with blockers.
  - Changes follow `project-manager.md` §5.6: canonical first, then the digest, in the same change.
- **Consequences:** Agents read the digest first and open the cited source for detail. If the two disagree, the canonical file wins and the difference is reported.

## ADR-005 — Money representation
- **Status:** ACCEPTED (2026-09-27), with precision and currency pending BLK-009
- **Decision:**
  - `Decimal`/`DecimalField` only, with an explicit `currency` on the order and ledger.
  - API money values are strings.
  - Order and item financial snapshots are persisted.
  - The ledger is append-only, with a unique idempotency key.
  - Rounding is `ROUND_HALF_UP` at line level *(to be confirmed with PM in BLK-003)*.
- **Source:** `00_core/05`, `00_core/06`.

## ADR-006 — Order state machine in the service layer
- **Status:** ACCEPTED (2026-09-27)
- **Decision:**
  - One transition table: `(from, to) → roles + guard`.
  - All changes go through `orders.services.transition_order()` inside `transaction.atomic()` with `select_for_update()`.
  - Each change writes `OrderStatusHistory`, schedules notifications with `on_commit`, and runs idempotently with an `Idempotency-Key`.
  - The API exposes `allowed_transitions`. A serializer never writes `status` directly.
- **Source:** `00_core/03`, `00_core/09`.

## ADR-007 — QA tests are black-box and live in `qa/`
- **Status:** ACCEPTED (2026-09-27). **Amended by ADR-018:** the "running backend" is the deployed server instance; QA suites execute on the server, never locally (REQ-009).
- **Decision:**
  - QA's automated tests run against a running backend over HTTP (pytest + httpx) in `qa/api/` and `qa/api/flows/`.
  - Frontend E2E uses Playwright in `qa/e2e/`.
  - Developer unit and API tests stay inside `backend/` and `frontend/`.
- **Consequences:** QA is independent of implementation internals, and QA never needs to edit application code. QA needs seed data. The backend provides a `seed_demo` management command (Backend task), and QA reviews it.

## ADR-008 — Frontend stack (Vue PWA)
- **Status:** ACCEPTED (2026-09-27). BLK-002 RESOLVED: the Vue 3 PWA is the MVP web client; Flutter later.
- **Decision:**
  - Vue 3 + TypeScript + Vite, Vue Router, Pinia, `vite-plugin-pwa`, Vitest + Vue Test Utils, ESLint + Prettier (+ `vue-tsc` type-check). Playwright for E2E (QA, `qa/e2e/`).
  - One API client module handles the envelope, JWT access/refresh (single refresh attempt on 401, then logout), the error codes and 429.
  - No UI component library in sprint-01 (plain scoped CSS + a small set of own components). A library can be chosen later through a new ADR.
  - **Build and serving:** `npm ci && npm run build` runs on the **local machine** (the server has no swap; ADR-015). The static `dist/` is shipped in the release and served by nginx at `https://${WEB_DOMAIN}` with an SPA fallback (`try_files $uri $uri/ /index.html`). There is no server-side frontend process and no frontend systemd unit.
  - **Configuration:** `VITE_API_BASE_URL` (value on the server build: `https://api.delivery.hossam-ameen.online`) and `VITE_APP_NAME` (`Flash`) are read at build time from the environment; nothing is hardcoded. `frontend/.env.example` documents them.
  - **Cross-origin:** the PWA and the API are different origins. The backend sets `CORS_ALLOWED_ORIGINS=https://${WEB_DOMAIN}` (django-cors-headers) and `CSRF_TRUSTED_ORIGINS=https://${WEB_DOMAIN},https://${API_DOMAIN}`. Auth uses the `Authorization: Bearer` header, not cookies, so no credentialed CORS is needed. The API also sets `CORS_EXPOSE_HEADERS = ["Retry-After"]` so the PWA can read the wait time on a cross-origin 429 (added 2026-09-27, TASK-007 review; api-contracts §1.1).
  - **Token storage (sprint-01):** access token in memory (Pinia), refresh token in `localStorage`. Revisit (httpOnly cookie) before real customer data exists; recorded as a known limitation.
  - **Refresh-failure policy** (TL decision 2026-09-27, TASK-007 review): a refresh that the API **rejects** (400/401) logs out and redirects to `/login?expired=1`; a refresh that is **not answered** (network error, 5xx, 429) fails the request but keeps the session. Recorded in api-contracts § Identity.
  - **Logout is client-side only** (no logout/blacklist endpoint in the MVP contract): the refresh token stays valid on the server until `JWT_REFRESH_TOKEN_LIFETIME_DAYS` expires. Known limitation together with the `localStorage` storage; both are revisited in one ADR (httpOnly cookie + simplejwt blacklist/logout endpoint) before real customer data exists.
  - **UI language:** English only (one keyed catalog, logical CSS properties ready for RTL) until BLK-009 decides languages; no i18n library until then.
- **Consequences:** Frontend work may start against the APPROVED Foundation contracts. Flutter (`mobile/`) is out of the MVP.

## ADR-009 — Python 3.13 runtime via Docker
- **Status:** SUPERSEDED by ADR-016 (2026-09-27). The server is now the reference runtime; local Docker is optional.
- **Original status:** ACCEPTED (2026-09-27)
- **Context:** `docs/standards/DRF_SKILL.md` requires Python 3.13+. The development machine has 3.12.3.
- **Decision:** Local Docker (`python:3.13-slim`) is the reference runtime for running and testing. Developers may use a local 3.13 venv if installed. Validation evidence must come from 3.13.

## ADR-010 — API paths and versioning
- **Status:** ACCEPTED (2026-09-27)
- **Decision:** Keep the `docs/standards/DRF_SKILL.md` paths (`/api/auth/…`, `/api/health/`, `/api/schema/`) with no URL version prefix for the MVP. Breaking changes after the first client release need a new ADR (a `/api/v2/` or header-based version).

## ADR-011 — Admin and Store surfaces
- **Status:** ACCEPTED (2026-09-27). BLK-002 RESOLVED: the PO named one MVP web client (the Vue PWA).
- **Decision:**
  - Django Admin/Jazzmin (at `https://${API_DOMAIN}/admin/`, staff only) serves internal staff operations from Sprint 1, at no extra cost.
  - The Admin MVP dashboard (`04_admin_dashboard/mvp_scope.md`) and the Store app are **role areas of the same Vue PWA**, backed by `/api/admin/…` and `/api/store/…`.
  - PWA route areas: `/customer/*`, `/driver/*`, `/store/*`, `/admin/*` (web domain; no clash with Django `/admin/`, which lives on the API domain). A route guard sends a logged-in user to the area of their `role`.
- **Rationale:** one client means one build, one deploy target, one API client and one QA E2E setup. Role areas are code-split, so a customer never downloads admin screens.
- **Rejected alternative:** Admin MVP entirely on Jazzmin. Quicker, but limits UX and custom dashboards. Jazzmin stays the staff back-office.
- **Consequences:** if the PO later wants a separate store or admin client, that is a new ADR and a PM escalation.

## ADR-012 — Infrastructure layout and ownership (adapts DRF_SKILL §3, §41–52)
- **Status:** ACCEPTED (2026-09-27). **Amended by ADR-015** (2026-09-27): the default and only implemented mode for sprint-01 is `systemd`; the `deploy/docker/**` and compose files are deferred (TASK-006 → BACKLOG), and `.github/` waits on BLK-012.
- **Context:**
  - `docs/standards/DRF_SKILL.md` places `docker/`, `deploy/` and `scripts/` inside `backend/`, and its Makefile mixes dev and deploy targets.
  - The agent-system spec (§25–49) adds a dedicated Infrastructure agent and a **repo-root** `deploy/` that must deploy the backend *and* the frontend.
  - DRF_SKILL §3 explicitly allows adapting the structure.
- **Decision:**
  ```
  deploy/
  ├── docker/
  │   ├── backend/      Dockerfile (python:3.13-slim, non-root), entrypoint.sh, wait_for_db.sh
  │   ├── frontend/     Dockerfile (node build → nginx static)
  │   └── compose/      local.yml, staging.yml, production.yml
  ├── nginx/            nginx.conf.template, backend.conf.template, frontend.conf.template
  ├── systemd/          backend.service.template (+ celery-worker/beat templates when enabled;
  │                     frontend.service.template only if a server-side frontend process exists)
  ├── scripts/          deploy.sh, deploy-backend.sh, deploy-frontend.sh, restart.sh, restart-backend.sh,
  │                     restart-frontend.sh, migrate.sh, health-check.sh, rollback.sh, setup-server.sh,
  │                     lib/common.sh (env loading, validation, logging, redaction, --dry-run)
  └── README.md
  .github/workflows/    backend.yml, frontend.yml, deploy.yml   (provider per BLK-012 / ADR-014)
  Makefile              ops targets (deploy, restart*, migrate, health, rollback, up/down local)
  .env.example          deployment variables (see below)
  backend/Makefile      developer targets from DRF_SKILL §45 (install, run, test, coverage, lint, …);
                        its docker-*/deploy-* targets delegate to the root Makefile
  backend/.env.example  application runtime variables (DRF_SKILL §8, §78)
  ```
  - Owners: `deploy/`, `.github/`, the root `Makefile` and the root `.env.example` belong to the **Infrastructure** agent. `backend/` belongs to Backend. `frontend/` belongs to Frontend.
  - **Two env files, one on the server:**
    - Locally, `.env` (deployment) and `backend/.env` (application) are separate.
    - On a server, both are merged in `${DEPLOY_PATH}/shared/.env`, which the compose `env_file` and the systemd `EnvironmentFile` both read.
  - **Variable naming** (spec §28 wins for deployment; DRF_SKILL names are kept for the application):
    - `SYSTEMD_SERVICE_NAME` → `BACKEND_SYSTEMD_SERVICE`
    - `BACKEND_PATH` → `${DEPLOY_PATH}/current/backend`
    - `FRONTEND_PATH` → `${DEPLOY_PATH}/current/frontend/dist`
    - `MEDIA_PATH` / `STATIC_PATH` → `${DEPLOY_PATH}/shared/{media,static}`
    - `DOMAIN`, `BACKEND_PORT` and `HEALTH_CHECK_PASSWORD` are unchanged
- **Consequences:**
  - TASK-006 (local Docker) moves from Backend to Infrastructure.
  - DRF_SKILL's deployment *requirements* (health check after deploy, templates, no hardcoding, Redis for throttling) still apply. Only their location changes.
  - `docs/standards/DRF_SKILL.md` itself is not edited.

## ADR-013 — Deployment modes, release layout, rollback and migrations
- **Status:** ACCEPTED (2026-09-27). BLK-011 RESOLVED. **Amended by ADR-015** (target server, systemd details, `AUTO_ROLLBACK`) and **ADR-017** (SQLite backup before every migrate; rollback may restore it).
- **Decision:**
  - **Mode:** `DEPLOYMENT_MODE=docker|systemd`, read from `.env` by every script. There is one command set for both modes.
  - **Transport:** SSH (`SERVER_USER@SERVER_HOST:SERVER_PORT`, key at `SSH_KEY_PATH`). The code is synced with `rsync` from a clean git checkout of a specific commit, or pulled on the server. Details are in the infra design.
  - **Releases:** `${DEPLOY_PATH}/{current, releases/<YYYYMMDD-HHMMSS>, shared/{.env, media, static, logs}}`, keeping `RELEASES_TO_KEEP` (default 5).
  - **Docker mode:**
    - images are tagged `flash-backend:<release>` and `flash-frontend:<release>`
    - order: `compose up -d` of the new tag → migrate (one-off `run --rm backend python manage.py migrate --noinput`) → health check
    - rollback: re-tag and start the previous release's images → health check
  - **systemd mode:**
    - new release dir → venv install → frontend assets built (in CI or on the server) → migrate → switch the `current` symlink → `systemctl restart ${BACKEND_SYSTEMD_SERVICE}` → `nginx -s reload` → health check
    - rollback: point `current` at the previous release → restart → health check
    - **"Previous release"** (clarified 2026-09-28, TASK-014 review) = the release that was `current` **before the last switch**, recorded at switch time in `releases/<id>/PREVIOUS` — never inferred from id/time order (which is wrong after a rollback + roll-forward). Without a recorded `PREVIOUS`, a bare rollback refuses and asks for an explicit target (TASK-017).
  - Gunicorn serves the backend in both modes. Celery worker/beat units or containers are started only when `CELERY_ENABLED` / `CELERY_BEAT_ENABLED`.
  - **Migrations are forward-only and must be backward-compatible with the previous release** (expand → deploy → contract). Rollback never runs reverse migrations. A migration that is not backward-compatible needs a TL-approved maintenance plan.
  - **Deploy fails** (non-zero exit, previous release kept) if the health check does not pass within `HEALTH_CHECK_TIMEOUT`. Automatic rollback on failure is controlled by `AUTO_ROLLBACK` (default `true` for staging and `false` for production, where it is reported for operator decision). *(Defaults to be confirmed with the PM.)*

## ADR-014 — CI/CD platform
- **Status:** PROPOSED (2026-09-27). Pending BLK-012 (git provider).
- **Proposal:**
  - GitHub Actions: `backend.yml` and `frontend.yml` run on push/PR with path filters, and `deploy.yml` deploys.
  - Staging deploys automatically on `main` when `AUTO_DEPLOY=true` (repo variable).
  - Production deploys through a `workflow_dispatch` or tag with a protected `production` environment that requires reviewer approval.
  - Security checks: `pip-audit`, `npm audit --audit-level=high`, secret scanning (gitleaks), and a container image scan (trivy).
  - Artifacts: the coverage report, the frontend `dist/`, and the image digests.
  - If the provider is GitLab or another platform, the same stages map onto its CI format.

## ADR-015 — Hosting and runtime on the shared VPS (systemd mode)
- **Status:** ACCEPTED (2026-09-27). Implements BLK-011 / REQ-008. Amends ADR-012 and ADR-013.
- **Context:** One GCP VPS (Ubuntu 24.04, `34.123.215.195`, user `hossam`, passwordless sudo, 2 vCPU, 3.8 GB RAM, **no swap**, ~13 GB free, nginx 1.24 + certbot present, no Docker). The server also runs the live **dental-clinic** app (nginx sites `*.dental.hossam-ameen.online`, `dental-clinic-backend.service` on `127.0.0.1:8000`, `/srv/dental-clinic`). Flash must never modify any of it.
- **Decision:**
  - **Mode:** `DEPLOYMENT_MODE=systemd` (set in the root `.env`). Scripts still read and validate the variable; `docker` exits non-zero with `docker mode is deferred (ADR-015)`. Docker must not be installed on the server.
  - **Transport:** operator-triggered `make deploy` from the local machine over SSH (`SERVER_USER=hossam`, `SERVER_HOST=34.123.215.195`, `SERVER_PORT=22`, `SSH_KEY_PATH=~/.ssh/id_ed25519`; path only, never echoed). `AUTO_DEPLOY=false`. There is no CI yet (BLK-012). **Exception to `infrastructure.md` §8 "no deploy without CI green":** until BLK-012 is resolved, the gate is TL code review + the backend suite green on the server (ADR-018) + QA PASS for release content. This is the only environment (production-like staging).
  - **Layout** (all owned by `hossam:hossam`, `DEPLOY_PATH=/srv/flash`):
    ```
    /srv/flash/
    ├── current -> releases/<YYYYMMDD-HHMMSS>      (atomic switch: ln -sfn tmp && mv -T)
    ├── releases/<id>/{backend/, frontend/dist/, venv/, REVISION}
    ├── shared/{.env (0600), db/, cache/, static/, media/, logs/, backups/}
    ├── sandbox/   (developer/TL backend test runs, ADR-018)
    └── qa/        (QA suite + its venv + results, ADR-018)
    ```
    **Permissions** (TL decision 2026-09-27, TASK-012 review; nginx runs as `www-data` and must reach `shared/static` and `shared/media` for the `/static/` and `/media/` aliases): `/srv/flash` 0755, `releases/` 0755, **`shared/` 0751** (others may traverse, not list), `shared/static` and `shared/media` 0755 (files 0644, public over HTTPS anyway), **`shared/db`, `shared/backups`, `shared/cache` 0700**, `shared/logs` 0750, `shared/.env` 0600, `sandbox/` and `qa/` 0750 (`qa/credentials.env` 0600). All owned `hossam:hossam`; no `www-data` group membership or group ownership is used (rejected alternative: group `www-data` on static/media would still need `shared` traversable by `www-data` plus setgid dirs, i.e. more moving parts for the same result). `setup-server.sh` enforces these modes idempotently.
    `RELEASES_TO_KEEP=5`, `DB_BACKUPS_TO_KEEP=5`. Deploy aborts before syncing if free disk on `/srv` < `MIN_FREE_DISK_MB` (default 1500).
  - **Release content:** built from a clean git checkout of one commit (`git archive <sha>`; a dirty tree is refused unless `--allow-dirty`, which is recorded in `REVISION`). The frontend is built **locally** (`npm ci && npm run build`) and only `dist/` is shipped. rsync uses `--link-dest` against the previous release to save disk. The server installs Python wheels only (uv, ADR-016); no npm/node build on the server.
  - **systemd unit** `flash-backend.service` (`BACKEND_SYSTEMD_SERVICE`), rendered from `deploy/systemd/backend.service.template`, installed to `/etc/systemd/system/`:
    - `User=hossam`, `Group=hossam`, `WorkingDirectory=${DEPLOY_PATH}/current/backend`, `EnvironmentFile=${DEPLOY_PATH}/shared/.env`
    - `ExecStart=${DEPLOY_PATH}/current/venv/bin/gunicorn config.wsgi:application --bind 127.0.0.1:${BACKEND_PORT} --workers ${GUNICORN_WORKERS} --threads ${GUNICORN_THREADS} --timeout ${GUNICORN_TIMEOUT} --max-requests 1000 --max-requests-jitter 100 --access-logfile - --access-logformat <no query string> --error-logfile -`
    - **Access log without query strings** (amended 2026-09-27, TASK-001/004 review): gunicorn's default access format logs the request line `%(r)s`, which includes the query string, so a `?password=` health request would reach journald. The unit must set an access log format that uses the path only (`%(U)s`), never `%(r)s` or `%(q)s`, e.g. `%({x-forwarded-for}i)s %(t)s "%(m)s %(U)s %(H)s" %(s)s %(b)s %(D)sus "%(a)s"`. In a systemd unit every `%` must be written `%%` (systemd specifiers); a gunicorn config file rendered next to the unit is an acceptable alternative.
    - defaults: `BACKEND_PORT=8010` (8000 is dental's), `GUNICORN_WORKERS=2`, `GUNICORN_THREADS=2`, `GUNICORN_TIMEOUT=30`
    - `Restart=always`, `RestartSec=5`, `WantedBy=multi-user.target` (enabled: survives reboot)
    - resource guard: `MemoryMax=${BACKEND_MEMORY_MAX}` (default `700M`), `TasksMax=128`
    - hardening: `NoNewPrivileges=true`, `PrivateTmp=true`, `ProtectSystem=full`, `ProtectHome=read-only` (the uv-managed Python lives in `~hossam/.local/share/uv`), `ReadWritePaths=${DEPLOY_PATH}/shared`
    - logs go to journald (`journalctl -u flash-backend`)
    - restart = `sudo systemctl restart flash-backend`. No Celery units (ADR-017).
  - **nginx:** exactly two site files, named after the Flash domains and nothing else: `/etc/nginx/sites-available/${API_DOMAIN}` and `/etc/nginx/sites-available/${WEB_DOMAIN}` (`api.delivery.hossam-ameen.online`, `delivery.hossam-ameen.online`), symlinked into `sites-enabled/`. Rendered from `deploy/nginx/api.conf.template` and `web.conf.template` with `envsubst` and an explicit variable list.
    - API site: `location /static/` → `alias ${DEPLOY_PATH}/shared/static/`; `/media/` → `alias ${DEPLOY_PATH}/shared/media/`; everything else `proxy_pass http://127.0.0.1:${BACKEND_PORT}` with `proxy_set_header Host $host`, `X-Forwarded-Proto $scheme`, and **`X-Forwarded-For $remote_addr` (overwrite, never append)**; `client_max_body_size 10m`. It defines its own `log_format flash_api` that logs `$uri` (not `$request`/`$args`) so a `?password=` health token can never reach an access log; logs to `/var/log/nginx/flash-api.*.log`.
    - Web site: `root ${DEPLOY_PATH}/current/frontend/dist`, `try_files $uri $uri/ /index.html`; `Cache-Control: no-cache` for `index.html`, `sw.js`, `manifest.webmanifest`; `/assets/` 1-year immutable; logs `/var/log/nginx/flash-web.*.log`.
    - Both: port 80 serves only `/.well-known/acme-challenge/` and a 301 to https; 443 `ssl` (**no `http2`**, see below) with the cert below and HSTS (`max-age=31536000`, no `preload`, no `includeSubDomains` — the parent domain is shared with dental).
    - **No HTTP/2 on the shared 443 socket** (amended 2026-09-27, BLK-013 RESOLVED, TL): on nginx 1.24 `http2` is a `listen` option of the whole `0.0.0.0:443`/`[::]:443` socket, which dental-clinic shares, so Flash's `http2` would switch **dental** to HTTP/2 as well. Flash therefore listens `443 ssl` only (`NGINX_HTTP2=off`, the only allowed value while dental shares the socket on nginx < 1.25.1). Re-enabling HTTP/2 needs a new ADR with PO **and** dental-owner consent (option B), or a separately approved nginx ≥ 1.25.1 upgrade using per-server `http2 on;` (option C). Evidence rule: `nginx -t` with Flash + live dental sites must show no `protocol options redefined` warning.
    - Two template phases: a `*.http.conf.template` bootstrap (port 80 only) used until the certificate exists, then the full template.
    - **Reload rule:** every change is `write → sudo nginx -t → (fail: restore the previous Flash files, nginx -t again, exit non-zero) → sudo systemctl reload nginx`. Never `nginx -s reload`/`systemctl reload nginx` without a passing `nginx -t` in the same step, never `systemctl restart nginx`, never edit `/etc/nginx/nginx.conf`, `conf.d/*`, `snippets/*` or any non-Flash site.
  - **TLS:** one certificate for exactly the two Flash domains:
    `sudo certbot certonly --nginx --cert-name flash-delivery -d ${API_DOMAIN} -d ${WEB_DOMAIN} --non-interactive --agree-tos [-m ${LETSENCRYPT_EMAIL}] --deploy-hook "nginx -t && systemctl reload nginx"`.
    `certonly` (not `install`) so certbot never edits our templates or any other site; the templates reference `/etc/letsencrypt/live/flash-delivery/{fullchain,privkey}.pem`. Renewal is covered by the existing `certbot.timer` (verified with `sudo certbot renew --dry-run --cert-name flash-delivery`, never a bare `certbot renew`). `LETSENCRYPT_EMAIL` comes from `.env` and is **optional** (amended 2026-09-27, TASK-012 review): the server already has a registered Let's Encrypt **production** ACME account, which certbot reuses when `-m` is omitted. When it is empty, `tls.sh` omits `-m`; if no production account exists (`sudo certbot show_account` fails), `tls.sh` fails early and asks for the email. Never `--register-unsafely-without-email`.
  - **Backend settings on the server** (Backend owns the code, values in `shared/.env`): `DJANGO_SETTINGS_MODULE=config.settings.production`, `DEBUG=False`, `ALLOWED_HOSTS=${API_DOMAIN},127.0.0.1,localhost`, `CORS_ALLOWED_ORIGINS=https://${WEB_DOMAIN}`, `CSRF_TRUSTED_ORIGINS=https://${API_DOMAIN},https://${WEB_DOMAIN}`, `SECURE_PROXY_SSL_HEADER=HTTP_X_FORWARDED_PROTO,https`, `NUM_PROXIES=1` (DRF client-IP resolution; nginx is the single trusted hop), `SECURE_SSL_REDIRECT=False` (nginx redirects; avoids redirect loops for the 127.0.0.1 health check), secure cookies on, `STATIC_ROOT=${DEPLOY_PATH}/shared/static`, `MEDIA_ROOT=${DEPLOY_PATH}/shared/media`.
  - **Env files:** the local root `.env` (from root `.env.example`) holds only deployment variables (host, user, key path, domains, ports, paths, service name, tuning) and **no application secrets**. The server's `shared/.env` holds the application variables (names = `backend/.env.example`) plus the few deployment values the unit/scripts need; it is rendered from `deploy/env/shared.env.template`. This refines ADR-012's "merged" wording: the merge happens only on the server.
  - **Secrets:** `setup-server.sh` creates `shared/.env` from `deploy/env/shared.env.template` on first run and **generates `SECRET_KEY` and `HEALTH_CHECK_PASSWORD` on the server** (`python3 -c 'import secrets…'`), `chmod 600`. They never leave the server, never appear in the repo, in local files, in script output or in logs. Existing values are never overwritten.
  - **sudo on the server** (confirmed 2026-09-27, TASK-013 review): Flash may run only `install -d` under `${DEPLOY_PATH}`; install/remove of `/etc/systemd/system/${BACKEND_SYSTEMD_SERVICE}.service` and the two Flash nginx site files + their `sites-enabled` links; `systemctl daemon-reload`; `systemctl enable|restart|stop|start|kill ${BACKEND_SYSTEMD_SERVICE}` (`stop`/`start` for the ADR-017 DB restore on rollback — never for any other unit); `systemctl reload nginx` after a passing `nginx -t`; `nginx -t` (also with `-c` on temp configs in `/tmp/flash-*`); certbot for `${CERT_NAME}` only; read-only `ss -p`, `certbot certificates|show_account`; Playwright `install-deps` (`--with-e2e` only).
  - **Health before the certificate exists** (accepted 2026-09-27, TASK-013 review): until `/etc/letsencrypt/live/${CERT_NAME}/` exists, the public checks use `http://` and the token endpoints are checked on `127.0.0.1` only (the health token is never sent over plain HTTP). Once the certificate exists, the https checks including the token endpoints are mandatory.
  - **Deploy order (systemd):** local preflight (env + clean tree + dental pre-snapshot) → build PWA locally → rsync release → `uv venv` + `uv pip install -r backend/requirements/production.txt` → `manage.py check --deploy` → `collectstatic --noinput` → SQLite backup (ADR-017) → `migrate --noinput` → switch `current` → `sudo systemctl restart flash-backend` → render nginx (if changed; reload rule above) → health check (ADR-015 health rules) within `HEALTH_CHECK_TIMEOUT` (default 60 s) → dental post-check → prune → report. **`AUTO_ROLLBACK=true`** for this environment (it is the only one, and a broken Flash site must not stay up); rollback is also available manually.
  - **Health check** (`health-check.sh`): runs on the server over SSH. `GET http://127.0.0.1:${BACKEND_PORT}/api/health/` and `/api/health/ready/` **and** the same through `https://${API_DOMAIN}`, header `X-Health-Check-Token` only (never `?password=`), token read from `shared/.env` inside the remote shell and passed to curl through stdin (`curl -H @- …`) so it is never in argv, output or logs; plus `https://${WEB_DOMAIN}/` 200 and containing the app root, `systemctl is-active flash-backend`, and `sudo nginx -t`.
  - **Dental non-interference guard** (`lib/dental_guard.sh`, called by setup/deploy/rollback/restart/tls): **pre and post** read-only snapshot of `sha256sum` of every non-Flash file **under all of `/etc/nginx/`** (amended 2026-09-27, TASK-012 review: dental's includes live in `/etc/nginx/dental-clinic/`, so the original `sites-*`/`conf.d`/`nginx.conf` list was too narrow), plus `/etc/letsencrypt/{options-ssl-nginx.conf,ssl-dhparams.pem}` and every `renewal/*.conf` except Flash's, and the dental unit's file hash, MainPID, start time and NRestarts; `systemctl is-active dental-clinic-backend`; HTTP status of `https://dental.hossam-ameen.online/` and `https://api.dental.hossam-ameen.online/`. Any difference fails the command loudly. Static preflight assertions: `BACKEND_PORT != 8000` and the port is free or held by `flash-backend`; `DEPLOY_PATH` not under `/srv/dental-clinic`; service name starts with `flash-`; nginx file names equal `API_DOMAIN`/`WEB_DOMAIN`, neither contains `dental`. Flash never reads or writes `/srv/dental-clinic`.
- **Consequences:** Resource use is bounded (2×2 gunicorn, `MemoryMax`, no builds on the server, pruning). The Docker mode, a separate production environment, PostgreSQL/Redis and CI remain deferred (FEAT-004 deferred criteria).

## ADR-016 — Python 3.13 on the server via `uv` (supersedes ADR-009)
- **Status:** ACCEPTED (2026-09-27)
- **Context:** `docs/standards/DRF_SKILL.md` requires Python 3.13+. The server has only python3.12 (Ubuntu 24.04); the local machine has 3.12.3; the PO requires the test suites to run on the server (REQ-009) and forbids Docker on the server.
- **Decision:**
  - `uv` is installed **for user `hossam` only** (no root, no apt changes, no system Python change) by `setup-server.sh`, pinned by `UV_VERSION` (installer `https://astral.sh/uv/${UV_VERSION}/install.sh`, into `~/.local/bin`). Then `uv python install --no-bin ${PYTHON_VERSION}` (default `3.13`) into `~/.local/share/uv/python` (`--no-bin`: no `python3.13` shim in `~/.local/bin`; scripts find the interpreter with `uv python find`). Idempotent.
  - Accepted user-level footprint (2026-09-27, TASK-012 review): `~/.local/bin/{uv,uvx}`, `~/.config/uv/uv-receipt.json` (written by the official installer), `~/.local/share/uv/**`, `~/.cache/uv/**`. Nothing system-wide.
  - **One venv per release:** `uv venv --python ${PYTHON_VERSION} ${DEPLOY_PATH}/releases/<id>/venv` + `uv pip install --python <venv> -r backend/requirements/production.txt`. The uv cache (`~/.cache/uv`) makes repeat installs fast and hardlinked. Rollback therefore needs no reinstall.
  - The **server is the reference runtime** for validation evidence (backend tests, `check`, `makemigrations --check`: ADR-018). Local Docker (TASK-006) is optional developer tooling and deferred to the backlog; it is not an acceptance gate. Developers may use a local 3.13 venv for editing convenience, but evidence must come from the server.
- **Consequences:** No change to dental's Python. Upgrading Python = change `PYTHON_VERSION`, deploy (new venv per release).

## ADR-017 — SQLite database and a Redis-free shared cache (deviation from DRF_SKILL §9, §70–71)
- **Status:** ACCEPTED (2026-09-27). PO decision (BLK-011): SQLite, no Redis, no new services.
- **Database:**
  - `DATABASE_URL=sqlite:////srv/flash/shared/db/flash.sqlite3` (outside releases, survives deploys). Config stays `DATABASE_URL`-driven (dj-database-url), so moving to PostgreSQL later is config + data migration.
  - When the engine is SQLite, settings add `OPTIONS = {"timeout": 20, "transaction_mode": "IMMEDIATE", "init_command": "PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL; PRAGMA busy_timeout=20000; PRAGMA foreign_keys=ON;"}` (Django ≥ 5.1) and `CONN_MAX_AGE=0`. WAL gives concurrent reads with the 2 gunicorn workers; `IMMEDIATE` avoids "database is locked" upgrade deadlocks.
  - **Backup before every migrate:** `migrate.sh` copies the DB with the SQLite online-backup API (`sqlite3.Connection.backup` of the server's system `python3` stdlib — amended 2026-09-27, TASK-013 review: independent of the release venv, same API, safe under WAL) to `shared/backups/flash-<release>-<UTC ts>.sqlite3` (0600), then runs `migrate --noinput`, and writes `releases/<id>/MIGRATION_STATE` recording the backup path and whether any migration was applied (`migrate --plan` non-empty). Keep `DB_BACKUPS_TO_KEEP` (5). No backup is taken when the DB does not exist yet (first deploy).
  - **Rollback:** switch `current` to the previous release → if the release being rolled back applied migrations, stop `flash-backend`, restore its pre-migrate backup (the current DB is first saved as `shared/backups/pre-rollback-<ts>.sqlite3`), start → health check. Controlled by `ROLLBACK_RESTORE_DB=auto|always|never` (default `auto`) and CLI `--restore-db` / `--no-restore-db`. Rollback prints a warning that writes made after the deploy are lost when the DB is restored. Reverse migrations are still never run (ADR-013).
  - **Revisit trigger:** before FEAT-009 (assignment concurrency) or the ledger (FEAT-011+), the TL raises an ADR for PostgreSQL; `select_for_update` is a no-op on SQLite.
- **Cache / throttling without Redis:**
  - `CACHES["default"]` comes from `RATELIMIT_CACHE_URL` (DRF_SKILL name kept), parsed by the backend helper `build_cache` in `backend/config/settings/_helpers.py` (a thin wrapper over django-environ's `cache_url`). Accepted values: `locmem://` (Flash's spelling, mapped to `LocMemCache` by the helper; django-environ's own scheme `locmemcache://` is accepted too), `filecache:///abs/path` and `redis://…`. Wording corrected 2026-09-27 (TASK-012 review): plain `environ.Env.cache_url` does **not** accept `locmem://`.
  - Server value: **`RATELIMIT_CACHE_URL=filecache:///srv/flash/shared/cache`** (Django `FileBasedCache`).
  - **Why FileBasedCache:** it is shared by all gunicorn workers on the host (throttle counters are consistent across the 2 workers, which LocMem is not); it needs no new service; and it keeps throttle writes **out of the SQLite database**, where `DatabaseCache` would add a write (and a writer lock) to every API request and contend with application writes. Limits accepted: no atomic increment (DRF's throttle is read-modify-write in every backend, so the counters are approximate under concurrency either way), and culling cost at `MAX_ENTRIES` (set `OPTIONS: {"MAX_ENTRIES": 10000}`), which is irrelevant at our traffic.
  - Production settings **refuse a LocMem cache (`locmem://` or `locmemcache://`)** (ImproperlyConfigured) because there are several workers. Tests keep an isolated LocMem cache cleared per test (DRF_SKILL §77).
  - `make throttle-reset` (Infrastructure) empties `shared/cache/` for QA reruns of the rate-limit suite; it never touches the DB.
- **Celery:** `CELERY_ENABLED=False`, `CELERY_BEAT_ENABLED=False` on the server; no broker, no worker units; readiness reports `"celery": "skipped"`. The code keeps the DRF_SKILL toggle for later.
- **Consequences:** DRF_SKILL's "Redis for production throttling" and "PostgreSQL in staging/production" are knowingly not met for sprint-01; everything else in DRF_SKILL applies.

## ADR-018 — QA and backend test suites run on the server
- **Status:** ACCEPTED (2026-09-27). Implements REQ-009 (PO: "do not run QA locally … backend test suites also run on the server; the local machine is for building only"). Amends ADR-007.
- **Decision:** one Infrastructure-owned runner, `deploy/scripts/remote-test.sh`, exposed as Make targets. It never touches `releases/`, `current` or `shared/db`:
  - **`make test-backend-remote [REF=<git ref>|WORKTREE=1]`** (developers, TL review, QA audit): ship `backend/` (from `git archive <ref>`, or the working tree with `WORKTREE=1` for in-progress work; excluding `.env`, `*.sqlite3`, venvs, caches) to `/srv/flash/sandbox/backend/`; venv `/srv/flash/sandbox/venv` (uv, Python 3.13, `requirements/development.txt`, re-synced only when requirements change); then runs, with an **explicit test environment** (`DJANGO_SETTINGS_MODULE=config.settings.development`, `DATABASE_URL=sqlite:////srv/flash/sandbox/test.sqlite3`, `RATELIMIT_CACHE_URL=locmem://` (understood by the backend helper, ADR-017), dummy `SECRET_KEY`/`HEALTH_CHECK_PASSWORD`, `CELERY_ENABLED=False`; `shared/.env` is **not** read): `ruff check .`, `ruff format --check .`, `python manage.py check`, `python manage.py makemigrations --check --dry-run`, `pytest --cov --cov-report=term-missing --cov-report=xml --cov-fail-under=80 --junitxml=…`. The output streams back; the coverage XML/JUnit are copied to local `backend/.remote-results/` (git-ignored). Non-zero exit on any failure.
  - **`make qa-remote [ARGS="-m smoke"]`** (QA): ship `qa/` to `/srv/flash/qa/suite/`; venv `/srv/flash/qa/venv` (uv, 3.13, `qa/requirements.txt`); run `pytest ${ARGS}` from the server against the **public HTTPS URLs** (`QA_BASE_URL=https://${API_DOMAIN}`, `QA_WEB_URL=https://${WEB_DOMAIN}`), with `QA_HEALTH_TOKEN` exported **only into the pytest process** from `shared/.env` (`HEALTH_CHECK_PASSWORD`) and QA user credentials from `/srv/flash/qa/credentials.env` (0600). Nothing secret is printed. Results (JUnit, logs, Playwright traces) are copied back to local `qa/.results/` (git-ignored) for the QA report.
  - **Implementation notes accepted in the TASK-012 review (2026-09-27):** sources are shipped as a **tar stream over SSH that is unpacked inside the server-side `flock`** (atomic replace of `sandbox/backend` or `qa/suite` while no other run uses it) instead of rsync; results are copied back with rsync into **one directory per run** (`backend/.remote-results/<run-id>/`, `qa/.results/<run-id>/`, plus a `latest` symlink), keeping the last 10 runs locally and on the server. Pytest uses the backend-owned `backend/pytest.ini` (`--ds=config.settings.test`, which wins over the exported `DJANGO_SETTINGS_MODULE`); `manage.py check`/`makemigrations` use `config.settings.development` from the explicit test env.
  - **`make seed-qa-users`**: runs TASK-003's `create_role_user` on the server to create/update `qa_customer`, `qa_driver`, `qa_store`, `qa_admin` (staff + superuser) with random passwords generated on the server into `/srv/flash/qa/credentials.env`. Passwords go to the command through stdin/env, never argv.
  - Playwright on the server: Chromium only (`playwright install --with-deps chromium` needs apt → done once by `setup-server.sh` via sudo only if QA's E2E is enabled; E2E runs headless with `--workers=1` to bound memory).
  - Rate-limit tests run last in a session (`-m ratelimit`), and QA runs `make throttle-reset` before and after them so it does not lock itself out.
- **Local machine:** builds only — the PWA build (with its lint, type-check and Vitest unit tests as build gates; they are not QA and not backend suites, so this is within REQ-009's wording — PM to confirm), shellcheck and template rendering. No pytest, no QA suites locally.
- **Consequences:** a server outage blocks testing; the sandbox and QA venvs cost ~300 MB disk, counted in the disk budget. The TL runs `make test-backend-remote REF=<commit>` in every backend code review.

## ADR-019 — Browser-safe status endpoint and OpenAPI access in production
- **Status:** ACCEPTED (2026-09-27)
- **Context:** the PWA status page must show whether the API is up, but `/api/health/` needs the `HEALTH_CHECK_PASSWORD`, which must never ship in a browser bundle. The Foundation contract left production OpenAPI access open.
- **Decision:**
  - New public endpoint **`GET /api/status/`**: no auth, `health`-scope throttle, returns `{"status": "ok"}` in the success envelope. No version, hostname, DB or config details. The PWA status page uses it (plus `/api/users/me/` when logged in). `/api/health/` and `/api/health/ready/` stay token-protected for infrastructure and QA only.
  - **OpenAPI in production:** `/api/schema/`, `/api/docs/`, `/api/redoc/` require a **staff** user (JWT bearer or admin session) when `API_DOCS_PUBLIC=False` (production default); public in development. Non-staff get 401/403 in the error envelope.
  - The docs views (`SchemaView`, `SwaggerView`, `RedocView`) live in `backend/common/openapi.py` next to the envelope/429 schema hook (shared OpenAPI infrastructure), not in an app.
  - Swagger UI and Redoc load their JavaScript from drf-spectacular's default CDN (jsdelivr). Accepted for staff-only docs (2026-09-27, TASK-004 review). Switch to `drf-spectacular-sidecar` (self-hosted assets) when a Content-Security-Policy is introduced or the docs must work offline.
- **Consequences:** recorded in `api-contracts.md` § Foundation; QA verifies schema access with the `qa_admin` token.
