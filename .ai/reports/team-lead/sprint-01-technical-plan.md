# Sprint 01 — Technical Plan (Team Lead)

- **Date:** 2026-09-27
- **Features:** FEAT-001 Backend Platform Foundation; FEAT-003 Frontend Foundation (conditional)
- **Inputs:** `DRF_SKILL.md` (CREATE mode, §4 order), ADR-001, 003, 007, 009, 010, `api-contracts.md` § Foundation

## 1. Design summary (FEAT-001)
Build `backend/` exactly per `DRF_SKILL.md` §3, limited to what the foundation needs.
- `config/` with split settings (`base`, `development`, `production`) and a test-friendly configuration. `pytest.ini` uses `config.settings.development`, with test overrides in `backend/tests/conftest.py`: LocMem cache, eager Celery off, and test health token.
- `common/`:
  - `BaseModel` plus soft delete and the Active/Deleted/All managers
  - `ApplicationError` hierarchy with a stable `code`
  - `custom_exception_handler`, which produces the standard envelope for every error type, including 429 and unexpected 500s without internals
  - response helpers and a renderer strategy so success responses are enveloped consistently
  - `StandardPagination` (envelope + count/next/previous/results)
  - throttle classes: `AuthRateThrottle`, `SensitiveRateThrottle`, `HealthRateThrottle`
- `apps/users/` — `User(AbstractUser)` + `Role` enum; `USERNAME_FIELD` per BLK-001; Jazzmin admin; JWT views with the `auth` throttle scope; role permission classes in `apps/users/permissions.py` (`IsCustomer`, `IsDriver`, `IsStoreUser`, `IsPlatformAdmin`).
- Health: `GET /api/health/` and `/api/health/ready/`. The health view lives in a small `apps/health/` app or `common/`; TASK-004 decides and documents the choice. It accepts the `X-Health-Check-Token` header (preferred) or `?password=`, uses a constant-time compare, never logs the token, and uses the dedicated `health` throttle scope.
- OpenAPI: drf-spectacular. Document the envelope and a 429 response globally through a spectacular postprocessing hook or extension. Schema/docs are public in development; production access is decided in TASK-004 and recorded in `api-contracts.md`.
- Celery: `config/celery.py` is loaded only when `CELERY_ENABLED=True`. The app must import and run without Redis.
- Cache: LocMem by default. `RATELIMIT_CACHE_URL` enables Redis (db 2) in staging and production.
- Docker (local only this sprint; **Infrastructure agent**, ADR-012): `deploy/docker/backend/Dockerfile` (`python:3.13-slim`), entrypoint (migrate → run), `wait_for_db.sh`, `deploy/docker/compose/local.yml`, and a root `Makefile` with `up`/`down`/`backend-test`.
- CI (**Infrastructure agent**, TASK-011, blocked on BLK-012): backend pipeline with lint → checks → tests with an 80% coverage gate → image build → security.

## 2. Task graph and execution order
Backend tasks run sequentially, because they share `config/settings/base.py` and `config/urls.py`. Infrastructure, QA and Frontend run in parallel on their own paths:

```
Backend:         TASK-001 ─► TASK-002 ─► TASK-005 ─► TASK-004 ─► TASK-003*     (*needs BLK-001)
Infrastructure:  (reads the plan on day 1, drafts the design) ─► TASK-006 once TASK-001 + TASK-005 land
                 ─► final check once TASK-003/004 land ─► TASK-011 once BLK-012 + git remote exist
QA:              TASK-008 from day 1 ─► TASK-009 after TASK-001…006 are READY_FOR_QA
Frontend:        TASK-007 BLOCKED on BLK-002 ─► TASK-010
```

## 3. File ownership this sprint
| Path | Owner task |
|---|---|
| `backend/manage.py`, `backend/config/**`, `requirements/`, `pytest.ini`, `Makefile`, `.env.example`, `.gitignore`, `README.md` | TASK-001 creates. Later tasks may **append** settings/URL entries in their own clearly delimited sections. |
| `backend/common/**`, `backend/tests/conftest.py` | TASK-002 |
| `backend/apps/users/**` | TASK-003 |
| Health module, spectacular/Jazzmin settings sections | TASK-004 |
| `backend/config/celery.py`, `config/__init__.py`, cache settings section | TASK-005 |
| `deploy/docker/backend/**`, `deploy/docker/compose/local.yml`, root `Makefile`, root `.env.example`, `deploy/README.md` | TASK-006 (Infrastructure) |
| `.github/workflows/backend.yml` | TASK-011 (Infrastructure) |
| `backend/Makefile` `docker-*` targets | TASK-001 creates them as delegations to the root Makefile (coordinated with TASK-006) |
| `frontend/**` | TASK-007 |
| `qa/**` | TASK-008, TASK-009 |

## 4. Reviews planned
| Task | Plan review | Why |
|---|---|---|
| TASK-002 | **Yes** | Sets the error codes, envelope and pagination conventions every endpoint inherits |
| TASK-003 | **Yes** | Auth architecture; user model is irreversible after the first migration (ADR-003) |
| TASK-006 | **Yes** | First infrastructure implementation of ADR-012; Docker architecture (spec §47) |
| TASK-011 | Code review only | CI/CD is always TL-reviewed (spec §47) |
| Others | No | Standard work fully specified by DRF_SKILL |

Code review uses the `templates/review.md` checklist, and I run `DRF_SKILL.md` §57 myself for every task.

## 5. Risks and technical notes
- **Envelope and DRF defaults:** make sure the browsable API, spectacular schema and simplejwt views are either enveloped consistently or explicitly excluded. Schema and docs endpoints are **not** enveloped.
- **Throttle tests** must use isolated LocMem caches cleared per test (`DRF_SKILL.md` §77). Never use a real Redis.
- **Health readiness:** Celery and Redis are checked only when enabled (§26).
- **Seed data for QA (ADR-007):** not in this sprint beyond the ability to create a user of each role (`createsuperuser` plus a documented management command or fixture from TASK-003).
