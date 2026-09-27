# Flash — Architecture

Owner: Team Lead. Status: **target architecture for a greenfield repo**. No application code exists as of 2026-09-27.
Decisions are recorded in `decisions.md`. Items marked *(proposed)* wait on an ADR or blocker.

## 1. System overview

```
 Customer ─┐                                       ┌─ Firebase (push, future, BLK-010)
 Driver  ──┼─ Vue PWA (frontend/) ─┐               │
 Store   ──┤  (store/admin surface: BLK-002)       │
 Admin   ──┘  Flutter (mobile/, later)             │
                                   │ HTTPS / JSON (JWT)
                                   ▼
                     Nginx ──► Django + DRF (backend/) ──► PostgreSQL (staging/prod) / SQLite (local)
                                   │
                                   └──► Redis (throttle cache; Celery broker when CELERY_ENABLED)
                                        Celery worker/beat (optional: notifications, assignment retries)
```

## 2. Repository layout (ADR-002)

```
delivery_project/
├── backend/                 # Django/DRF, structured exactly per DRF_SKILL.md §3
├── frontend/                # Vue PWA (ADR-008, proposed)
├── mobile/                  # Flutter (later phase)
├── qa/                      # QA-owned black-box API + E2E tests, test plans (ADR-007)
│   ├── api/  api/flows/  e2e/  plans/
├── deploy/                  # Infrastructure-owned: docker, nginx, systemd, scripts, README (ADR-012)
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
- Python 3.13, Django, DRF, simplejwt, drf-spectacular, Jazzmin, django-environ, dj-database-url
- pytest, pytest-django, pytest-cov, ruff
- Docker and Docker Compose

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
- `/api/auth/…` (token, refresh, register) · `/api/health/`, `/api/health/ready/` · `/api/schema/`, `/api/docs/`, `/api/redoc/`
- `/api/users/me/`, `/api/customer/addresses/`
- `/api/stores/…` (public browse)
- `/api/store/…` (store-owner management: catalog, orders)
- `/api/orders/…` (customer)
- `/api/driver/…` (assignments, actions)
- `/api/admin/…` (admin dashboard APIs), plus Django Admin/Jazzmin at `/admin/` for staff operations

### 3.5 Environments
| | Local | Staging | Production |
|---|---|---|---|
| DB | SQLite (or Postgres via docker) | PostgreSQL | PostgreSQL |
| Cache/throttle | LocMem | Redis db 2 | Redis db 2 |
| Celery | disabled | enabled if needed | enabled if needed |
| Serving | runserver / `make up` (compose local) | `DEPLOYMENT_MODE` docker or systemd, + nginx | same (BLK-011) |

### 3.6 Deployment (ADR-012, ADR-013, ADR-014)
```
Developer push ─► CI (lint → test → build → security) ─► [staging: auto if AUTO_DEPLOY] / [production: approval]
                                                            │
                                                            ▼  deploy/scripts/deploy.sh (SSH)
     Server ${DEPLOY_PATH}: releases/<ts> ─► migrate (forward-only) ─► switch current / start new images
                                                            │
                                                            ▼
                     health-check.sh: /api/health/, /api/health/ready/ (X-Health-Check-Token), frontend /, nginx, services
                                                            │ fail
                                                            ▼
                                                   rollback.sh (previous release / image)
```
- One command set for both `DEPLOYMENT_MODE=docker|systemd`: `make deploy | restart | migrate | health | rollback`.
- Nginx: TLS termination, `/api/` and `/admin/` → gunicorn `127.0.0.1:${BACKEND_PORT}`, `/static/` and `/media/` from `shared/`, `/` → the SPA `dist/` with `try_files … /index.html`.
- **Trusted proxy:** Django trusts `X-Forwarded-For` only from Nginx. This is needed for correct throttling by IP (DRF_SKILL §74). Backend and Infrastructure coordinate it through the TL.

## 4. Frontend *(proposed, ADR-008, pending BLK-002)*
- Vue 3 + TypeScript + Vite + Vue Router + Pinia + `vite-plugin-pwa`; Vitest for unit tests; Playwright (QA) for E2E.
- One API client module handles the envelope, JWT refresh and error mapping.
- Role-based route areas: `/customer/*`, `/driver/*`. Store and admin areas are decided in BLK-002.
- There is no business logic in the client (REQ-001, REQ-037).

## 5. Testing architecture
- Developer tests: `backend/apps/<app>/tests/` and `backend/tests/` (pytest), plus `frontend/**/*.spec.ts` (Vitest).
- QA tests: `qa/` (black-box via HTTP against a running stack), and Playwright E2E (ADR-007).
- Coverage gate: ≥ 80% backend (DRF_SKILL §36).

## 6. Known constraints and risks
- The local machine has Python 3.12.3, but the standard requires 3.13+. Use Docker (`python:3.13-slim`) or install 3.13 (ADR-009).
- CI/CD needs a git remote. The provider is unknown (BLK-012).
- The repository is **not under git**. Code review, diffs and rollback all depend on version control → setup action in Sprint 1.
- Many financial and cancellation rules are undefined (BLK-003/004/005). The foundation and catalog can proceed; ordering and money cannot.
