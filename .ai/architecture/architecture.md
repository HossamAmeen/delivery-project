# Flash — Architecture

Owner: Team Lead. Status: **target architecture for a greenfield repo**. No application code exists as of 2026-09-27. Revised 2026-09-27 for the PO hosting decisions (ADR-015…019).
Decisions are recorded in `decisions.md`. Items marked *(proposed)* wait on an ADR or blocker.

## 1. System overview

```
 Customer ─┐                                          ┌─ Firebase (push, future, BLK-010)
 Driver  ──┼─ Vue PWA (frontend/, ADR-008/011)         │
 Store   ──┤  https://delivery.hossam-ameen.online     │
 Admin   ──┘  Flutter (mobile/, after MVP)             │
                                   │ HTTPS / JSON (JWT Bearer, CORS)
                                   ▼
   nginx (shared with dental) ──► gunicorn 127.0.0.1:8010 (flash-backend.service) ──► SQLite (WAL, shared/db)
   https://api.delivery.hossam-ameen.online          │
                                                     └──► FileBasedCache (shared/cache) for throttling
                                                          Celery: disabled (ADR-017)
```
Sprint-01 target: one shared VPS, systemd mode, no Docker, SQLite, no Redis (ADR-015, ADR-016, ADR-017). PostgreSQL/Redis/Celery are the planned upgrade path before assignment/ledger features.

## 2. Repository layout (ADR-002)

```
delivery_project/
├── backend/                 # Django/DRF, structured exactly per DRF_SKILL.md §3
├── frontend/                # Vue PWA (ADR-008, ACCEPTED)
├── mobile/                  # Flutter (later phase)
├── qa/                      # QA-owned black-box API + E2E tests, test plans (ADR-007)
│   ├── api/  api/flows/  e2e/  plans/
├── deploy/                  # Infrastructure-owned: nginx, systemd, scripts, README (ADR-012/015; docker/ deferred)
├── .github/workflows/       # CI/CD (ADR-014, pending BLK-012)
├── Makefile                 # ops targets (Infrastructure); backend/Makefile holds dev targets
├── .env.example             # deployment variables; backend/.env.example holds app variables
├── flash_business_logic/    # canonical business rules (PM/PO)
├── 06_brand/                # brand assets (duplicate of flash_business_logic/06_brand)
├── DRF_SKILL.md             # backend engineering standard
├── .ai/                     # team operating system
├── .claude/agents/          # Claude Code subagent entry points
└── CLAUDE.md
```

Deployment and container files live in the repo-root `deploy/`, not in `backend/` (ADR-012 adapts DRF_SKILL §3). The Infrastructure agent owns them.

## 3. Backend

### 3.1 Standard
`DRF_SKILL.md` in CREATE mode:
- Python 3.13 (uv-managed on the server, ADR-016), Django ≥ 5.1, DRF, simplejwt, drf-spectacular, Jazzmin, django-environ, dj-database-url, django-cors-headers, gunicorn
- pytest, pytest-django, pytest-cov, ruff
- Docker/Compose: optional local tooling only, deferred (TASK-006 BACKLOG)

Settings are split into `base`, `development` and `production`, with all configuration from `.env`.

### 3.2 Django apps *(proposed; each app is confirmed in the feature design that introduces it)*
| App | Owns | Key models |
|---|---|---|
| `users` | Identity, roles, profiles, addresses | `User` (custom, `role`), `CustomerProfile`, `DriverProfile`, `Address` |
| `stores` | Stores and catalog | `Store`, `StoreCategory`, `Product` |
| `orders` | Order aggregate and lifecycle | `Order`, `OrderItem`, `OrderStatusHistory`; `OrderStatus` enum; transition service |
| `assignments` | Driver assignment | `DriverAssignment`; assignment service (strategy pluggable) |
| `payments` | Collection, fees, ledger | `Collection`, `LedgerAccount`?, `LedgerEntry` |
| `notifications` | Notification records and delivery | `Notification`; `NotificationService` + providers |
| `audit` | Audit trail | `AuditLog` |
| `common/` (not an app) | Shared infrastructure | `BaseModel`, managers, exception handler, responses, pagination, permissions, throttling |

Dependency direction:
- `orders` → `stores`, `users`
- `assignments` → `orders`, `users`
- `payments` → `orders`
- `notifications` and `audit` are called by the other apps and never call back into them

### 3.3 Cross-cutting patterns
1. **Custom user model from the first migration** (ADR-003). `AUTH_USER_MODEL = "users.User"`, with a `role` choice field: CUSTOMER, DRIVER, STORE, ADMIN.
2. **Services / selectors.**
   - Writes that carry business meaning go through `services.py`: `place_order()`, `transition_order()`, `assign_driver()`, `complete_delivery()`.
   - Complex reads go in `selectors.py`.
   - Views stay thin.
3. **Order state machine** (ADR-006):
   - a single `TRANSITIONS` table: `(from_status, to_status) → allowed actor roles + guard function`
   - `transition_order(order_id, to_status, actor, payload, idempotency_key)` runs `atomic` + `select_for_update`, then guard → update → `OrderStatusHistory` → side effects (`on_commit` notifications, ledger)
   - `allowed_transitions(order, actor)` is exposed in the API
4. **Money** (ADR-005):
   - `DecimalField(max_digits=12, decimal_places=<per currency, BLK-009>)` plus a `currency` field
   - serialized as strings
   - snapshots are stored on `Order`/`OrderItem`
5. **Ledger:**
   - append-only `LedgerEntry` with `unique(idempotency_key)`
   - balances come from aggregation, optionally with a cached balance that is reconciled against the ledger
6. **Idempotency:**
   - mutating endpoints with retry risk (place order, transitions, completion) accept an `Idempotency-Key` header
   - DB unique constraints are the last line of defense
7. **Notifications:**
   - `NotificationService.notify(event, recipients, payload)` persists `Notification` rows
   - provider delivery is dispatched `on_commit`, through Celery when enabled and synchronously and fail-safe otherwise
8. **Audit:**
   - a service-level `audit.record(actor, action, target, before, after)` called from the services
   - no signals-magic for business audit
9. **Soft delete:**
   - `BaseModel.deleted_at` plus Active/Deleted/All managers (DRF_SKILL §11–13)
   - orders and ledger entries are **never** soft-deleted; they use terminal statuses and reversal entries instead
10. **Permissions:**
    - role permission classes (`IsCustomer`, `IsStoreUser`, `IsDriver`, `IsPlatformAdmin`)
    - plus queryset scoping per role, plus object-level checks
    - out-of-scope objects return 404, which avoids leaking that they exist

### 3.4 API surface (base paths; details in `api-contracts.md`)
- `/api/auth/…` (token, refresh; register in FEAT-002) · `/api/status/` (public, ADR-019) · `/api/health/`, `/api/health/ready/` · `/api/schema/`, `/api/docs/`, `/api/redoc/`
- `/api/users/me/`, `/api/customer/addresses/`
- `/api/stores/…` (public browse)
- `/api/store/…` (store-owner management: catalog, orders)
- `/api/orders/…` (customer)
- `/api/driver/…` (assignments, actions)
- `/api/admin/…` (admin dashboard APIs), plus Django Admin/Jazzmin at `/admin/` for staff operations

### 3.5 Environments
| | Local (build machine) | Server (only environment; production-like staging) |
|---|---|---|
| Purpose | edit + build (PWA build, shellcheck, template render). **No test suites** (REQ-009) | runs the app, the backend suite (sandbox) and QA (ADR-018) |
| Python | 3.12 system (editing only) | 3.13 via uv, venv per release (ADR-016) |
| DB | — | SQLite `shared/db/flash.sqlite3`, WAL (ADR-017) |
| Cache/throttle | — | `filecache:///srv/flash/shared/cache` (ADR-017) |
| Celery | — | disabled |
| Serving | — | systemd `flash-backend` (gunicorn 2×2 on 127.0.0.1:8010) + nginx + Let's Encrypt (ADR-015) |

### 3.6 Deployment (ADR-012, ADR-013, ADR-015, ADR-016, ADR-017; CI ADR-014 pending BLK-012)
```
Operator (local) ─ make deploy ─► preflight: .env valid, clean git tree, dental pre-snapshot, disk ≥ MIN_FREE_DISK_MB
        │  build PWA locally (npm ci && npm run build, VITE_API_BASE_URL)
        ▼  rsync (SSH, --link-dest) git-archive(backend) + frontend/dist
Server /srv/flash/releases/<ts>/ ─► uv venv (3.13) + pip install ─► check --deploy ─► collectstatic
        ─► SQLite online backup → shared/backups ─► migrate (forward-only) ─► switch current (atomic)
        ─► systemctl restart flash-backend ─► [nginx render → nginx -t → reload]
        ─► health-check.sh: 127.0.0.1:8010 + https://api… /api/health/ + /ready/ (header token via stdin),
                            https://delivery… /, systemctl is-active, nginx -t
        ─► dental post-check (unchanged) ─► prune (5 releases, 5 DB backups) ─► report
                │ fail
                ▼
        rollback.sh (AUTO_ROLLBACK=true): previous release [+ restore pre-migrate DB when migrations ran] → restart → health
```
- One command set: `make setup-server | deploy | restart [backend|frontend|all] | migrate | health | rollback | tls | test-backend-remote | qa-remote | seed-qa-users | throttle-reset`. Every script supports `--dry-run` and redacts secrets.
- `DEPLOYMENT_MODE` is read from `.env`; only `systemd` is implemented (ADR-015).
- nginx: two site files named `api.delivery.hossam-ameen.online` and `delivery.hossam-ameen.online`. API site → gunicorn `127.0.0.1:${BACKEND_PORT}`, `/static/` and `/media/` from `shared/`. Web site → `current/frontend/dist` with `try_files … /index.html`. TLS via `certbot certonly --nginx --cert-name flash-delivery` for exactly the two domains.
- **Trusted proxy:** nginx overwrites `X-Forwarded-For` with `$remote_addr` and sets `X-Forwarded-Proto`; Django uses `NUM_PROXIES=1` and `SECURE_PROXY_SSL_HEADER` (DRF_SKILL §74).
- **Co-hosting:** the dental-clinic app (`/srv/dental-clinic`, `dental-clinic-backend.service`, port 8000, its nginx sites) is never modified; a guard snapshots it before and after every Flash operation (ADR-015).

## 4. Frontend (ADR-008, ADR-011, ACCEPTED)
- Vue 3 + TypeScript + Vite + Vue Router + Pinia + `vite-plugin-pwa`; Vitest for unit tests; Playwright (QA) for E2E.
- One API client module handles the envelope, JWT refresh and error mapping. `VITE_API_BASE_URL` is set at build time.
- Role-based route areas `/customer/*`, `/driver/*`, `/store/*`, `/admin/*` in one app (ADR-011), plus `/login` (username + password) and `/status` (calls `GET /api/status/`, ADR-019).
- Static build served by nginx at `https://delivery.hossam-ameen.online`; built on the local machine.
- There is no business logic in the client (REQ-001, REQ-037).

## 5. Testing architecture (ADR-018)
- Developer tests: `backend/apps/<app>/tests/` and `backend/tests/` (pytest), executed **on the server** with `make test-backend-remote` (sandbox venv, isolated test DB/cache). `frontend/**/*.spec.ts` (Vitest) runs as a build gate on the local machine.
- QA tests: `qa/` (black-box via HTTPS against the deployed instance) and Playwright E2E, executed on the server with `make qa-remote` (ADR-007, ADR-018).
- Coverage gate: ≥ 80% backend (DRF_SKILL §36), measured on the server's Python 3.13.

## 6. Known constraints and risks
- The server is shared with a live third-party app (dental-clinic). All Flash operations go through the guarded scripts (ADR-015).
- 3.8 GB RAM, no swap: no builds on the server, bounded gunicorn, `MemoryMax`.
- SQLite + FileBasedCache are accepted deviations from DRF_SKILL (ADR-017); revisit before FEAT-009/ledger.
- CI/CD needs a git remote; the provider is unknown (BLK-012). Until then deploys are operator-triggered with TL review + server test evidence as the gate.
- The repository is under git (`main`, initial commit `8b5dc17`) with no remote.
- Many financial and cancellation rules are undefined (BLK-003/004/005). The foundation and catalog can proceed; ordering and money cannot.
