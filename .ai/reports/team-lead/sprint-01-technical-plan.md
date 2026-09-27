# Sprint 01 — Technical Plan (Team Lead)

- **Date:** 2026-09-27 (revision 2 — replaces the first plan after the PO decisions of 2026-09-27)
- **Features:** FEAT-001 Backend Platform Foundation · FEAT-003 Frontend Foundation (Vue PWA, unconditional) · FEAT-004 Deployment & Environments (systemd, shared VPS)
- **Inputs:** `DRF_SKILL.md` (CREATE mode), sprint-01 handoff, BLK-001/002/011 RESOLVED, BLK-012 partial, REQ-008, REQ-009
- **Decisions (this revision):** ADR-008 ACCEPTED, ADR-009 SUPERSEDED, ADR-011 ACCEPTED, ADR-012/013 amended, new ADR-015 (hosting/runtime), ADR-016 (Python 3.13 via uv), ADR-017 (SQLite + FileBasedCache, no Redis/Celery), ADR-018 (tests on the server), ADR-019 (`/api/status/`, staff-only docs in production)
- **Contracts:** `api-contracts.md` § Foundation and § Identity are **APPROVED** (username + password, `/api/users/me/`, `/api/status/`, error codes). Frontend may start.

## 1. What changed vs. revision 1
| Area | Before | Now |
|---|---|---|
| Runtime / reference | local Docker `python:3.13-slim` | the server, Python 3.13 via `uv` (ADR-016); local Docker deferred (TASK-006 → BACKLOG) |
| Where tests run | local Docker | **server only** — `make test-backend-remote`, `make qa-remote` (ADR-018) |
| DB / cache | Postgres + Redis in staging/prod | SQLite WAL in `shared/db` + FileBasedCache in `shared/cache`; Celery disabled (ADR-017) |
| Deployment | sprint-02 | sprint-01: systemd on the shared VPS, nginx + Let's Encrypt, two domains (ADR-015) |
| Login | pending BLK-001 | username + password; `/api/users/me/` added |
| Frontend | blocked | TODO: login, status page (`/api/status/`), role-area shell, branding |
| CI | TASK-011 | still BLOCKED (BLK-012); gate = TL review + server tests + QA PASS (ADR-015) |

## 2. Design summary

### 2.1 Backend (FEAT-001 + FEAT-004 backend pieces)
- Structure per `DRF_SKILL.md` §3: `config/` split settings, `common/`, `apps/users/`, `apps/health/`.
- Settings additions for the server (TASK-001): SQLite `OPTIONS` (WAL, IMMEDIATE, busy timeout), CORS for the web origin, CSRF trusted origins, proxy/HTTPS headers, static/media roots in `shared/`, `API_DOCS_PUBLIC`, gunicorn in production requirements, Django ≥ 5.1.
- Envelope: default `EnvelopeJSONRenderer` + `custom_exception_handler`; stable `errors.code` table in `api-contracts.md` (TASK-002).
- Cache from `RATELIMIT_CACHE_URL` (`locmem://` tests, `filecache:///srv/flash/shared/cache` server); production refuses LocMem; `NUM_PROXIES=1` behind nginx (TASK-005).
- Health (`/api/health/`, `/ready/`, token header), public `/api/status/`, OpenAPI staff-only in production, Jazzmin (TASK-004).
- `users.User(AbstractUser)` + `role`, username login, JWT token/refresh with contract errors, `/api/users/me/`, role permissions, `create_role_user` (password via stdin/env) (TASK-003).

### 2.2 Frontend (FEAT-003)
Vite + Vue 3 + TS PWA: API client (envelope, single refresh, error codes, 429), Pinia auth store, `/login`, `/status`, lazy role areas `/customer|driver|store|admin`, state components, PWA manifest/icons from `06_brand/flash_initial_logo.png`. Built locally with `VITE_API_BASE_URL=https://api.delivery.hossam-ameen.online`; `dist/` served by nginx (TASK-007).

### 2.3 Infrastructure (FEAT-004)
`/srv/flash/{current,releases,shared,sandbox,qa}`; `flash-backend.service` (gunicorn 2 workers × 2 threads on `127.0.0.1:8010`, `MemoryMax=700M`); nginx site files named `api.delivery.hossam-ameen.online` and `delivery.hossam-ameen.online`; `certbot certonly --nginx --cert-name flash-delivery` for exactly those two names; safe-apply (`nginx -t` before every reload, restore on failure); SQLite backup before every migrate; rollback with optional DB restore; dental guard snapshot before/after every operation (ADR-015). Tooling in TASK-012 (bootstrap + remote test runners) and TASK-013 (full tooling), executed in TASK-014.

### 2.4 QA (all three features)
Harness and plans from day 1 (TASK-008); everything executes on the server via `make qa-remote` against the public HTTPS URLs, with QA users from `make seed-qa-users` (TASK-009, TASK-010, TASK-015).

## 3. Execution order and parallelization

```
Wave 0 (now, parallel)
  Infrastructure: TASK-012 bootstrap + remote runners ──────────────┐ (unblocks server validation)
  Frontend:       TASK-007 PWA scaffold ─────────────────────────────┼──────────────┐
  QA:             TASK-008 strategy, plans, harness ─────────────────┼──────┐       │
  Backend:        TASK-001 (coding may start now; validate after 012)│      │       │
                                                                     ▼      │       │
Wave 1 (parallel lanes)                                                     │       │
  Backend (sequential, shared settings/urls):                               │       │
      TASK-001 → TASK-002 → TASK-005 → TASK-004 → TASK-003                   │       │
  Infrastructure: TASK-013 deploy tooling (after 012)                        │       │
  TL: review each task as it reaches READY_FOR_REVIEW                       │       │
                                                                            ▼       ▼
Wave 2  Infrastructure: TASK-014 server setup + deploy + TLS + seed + rollback exercise
        (needs 013, 001–005 and 007 all READY_FOR_QA)
                                                                            │
Wave 3 (parallel on the server; rollback window of 015 first or last)       ▼
  QA: TASK-015 FEAT-004 · TASK-009 FEAT-001 · TASK-010 FEAT-003
                                                                            │
Wave 4  TL final review → READY_FOR_RELEASE → PM acceptance
Blocked: TASK-011 (BLK-012). Backlog: TASK-006.
```

### Agent → task queue
| Agent | Tasks, in order | Parallel with |
|---|---|---|
| Infrastructure | TASK-012 → TASK-013 → (wait) → TASK-014 → TASK-017 (rollback target from deploy history; before TASK-015's rollback step) | everything in waves 0–1 |
| Backend | TASK-001 → TASK-002 → TASK-005 → TASK-004 → TASK-003 (strictly sequential) → TASK-016 (`create_role_user --inactive`, added 2026-09-27 from TASK-008) | Infra, Frontend, QA |
| Frontend | TASK-007 | Backend, Infra, QA |
| QA | TASK-008 (wave 0) → TASK-015, TASK-009, TASK-010 (wave 3) | wave 0–1 with all |
| Team Lead | reviews on each READY_FOR_REVIEW (backend validation via `make test-backend-remote REF=<sha>`), final sign-off | — |

Backend coding of TASK-001 can start immediately; its move to READY_FOR_REVIEW waits only for TASK-012's runner.

## 4. File ownership this sprint
| Path | Owner task |
|---|---|
| `backend/manage.py`, `backend/config/**` (skeleton, split settings, CORS/proxy/SQLite options), `backend/requirements/`, `pytest.ini`, `backend/Makefile`, `backend/.env.example`, `backend/.gitignore`, `backend/README.md` | TASK-001 creates; later backend tasks **append** in their delimited sections |
| `backend/common/**`, `backend/tests/conftest.py`, DRF section | TASK-002 |
| Cache/Celery/proxy sections, `backend/config/celery.py`, `config/__init__.py` | TASK-005 |
| `backend/apps/health/**`, OpenAPI/Jazzmin/Health sections, their URLs | TASK-004 |
| `backend/apps/users/**`, AUTH/JWT sections, auth + users URLs | TASK-003 |
| `frontend/**` | TASK-007 |
| `deploy/scripts/lib/**`, `setup-server.sh` (bootstrap), `remote-test.sh`, root `Makefile`, root `.env.example`, root `.gitignore` (append 3 lines) | TASK-012, then TASK-013 extends |
| `deploy/scripts/**` (rest), `deploy/nginx/**`, `deploy/systemd/**`, `deploy/env/**`, `deploy/README.md` | TASK-013 (TASK-014 may fix, reviewed) |
| `qa/**` | TASK-008 → TASK-009/010/015 (same agent, coordinate within QA) |
| `.ai/reports/infrastructure/**` | TASK-012/013/014 |
| `.ai/architecture/**`, `.ai/reports/team-lead/**` | TL (backend adds error codes through the TL) |

No two agents share a path at the same time. Backend tasks are sequential because they share `config/settings/base.py` and `config/urls.py`.

## 5. Build / runtime contracts between agents
| Contract | Producer | Consumer |
|---|---|---|
| `backend/requirements/production.txt`, `config.wsgi:application`, env names in `backend/.env.example` | TASK-001 | TASK-013 (`shared.env.template`, unit) |
| `manage.py create_role_user --username --role [--staff --superuser --update] --password-stdin` (+ `--inactive` from TASK-016) | TASK-003, TASK-016 | TASK-013 `seed-qa-users.sh` (incl. `qa_inactive`) |
| `/api/health/`, `/api/health/ready/` (header token), `/api/status/` | TASK-004 | TASK-013 `health-check.sh`, TASK-007 status page, QA |
| `npm ci && npm run build` in `frontend/`, env `VITE_API_BASE_URL`, output `frontend/dist`, `base '/'` | TASK-007 | TASK-013 `deploy-frontend.sh` |
| `make test-backend-remote [REF=|WORKTREE=1]`, `make qa-remote ARGS=`, `make seed-qa-users`, `make throttle-reset` | TASK-012/013 | Backend, TL, QA |

## 6. Reviews planned
| Task | Plan review | Mode |
|---|---|---|
| TASK-002 | Yes | **pre-approved (conditional)** — envelope renderer + error code table fixed in the task/contract |
| TASK-003 | Yes | **pre-approved (conditional)** — contract fixed (username + password) |
| TASK-007 | Yes | **pre-approved (conditional)** — ADR-008/011/019 |
| TASK-012, TASK-013, TASK-014 | Yes (shared production server) | **pre-approved (conditional)** — constraints embedded in each task; TL reviews the implementation/evidence |
| TASK-001, 004, 005 | No | code review only |
| TASK-008/009/010/015 | No | QA |

Pre-approval is conditional: any deviation from the written constraints requires TL approval before coding. Code review always runs the validation myself: backend via `make test-backend-remote REF=<sha>` (ruff, check, makemigrations --check, pytest ≥ 80%); frontend via the build gates (lint, type-check, unit, build) on the local build machine; infrastructure via shellcheck, dry-runs, the temp-config `nginx -t` and `systemd-analyze verify` on the server (infrastructure.md §6), and for TASK-014 the deployment evidence plus a `make health`.

## 7. Risks and technical notes
- **Shared server:** every Flash operation goes through the guarded scripts; any dental guard difference stops the work (TASK-014 notes).
- **Memory, no swap:** no builds on the server; gunicorn 2×2, `MemoryMax=700M`; Playwright E2E with one worker.
- **SQLite:** WAL + IMMEDIATE + busy timeout; backup before migrate; revisit (PostgreSQL ADR) before FEAT-009 / ledger.
- **Throttle counters** in FileBasedCache are approximate under concurrency (as with any DRF throttle); acceptable. QA uses `make throttle-reset` around rate-limit tests.
- **Health token hygiene:** header only in tooling; nginx log format excludes query strings; token passed to curl via stdin.
- **No CI (BLK-012):** the release gate is TL review + server test evidence + QA PASS. TASK-011 resumes when a remote exists.
- **Envelope and DRF defaults:** schema/docs views are raw; simplejwt errors are wrapped to the contract codes.
- **Seed data:** QA users only (`qa_customer`, `qa_driver`, `qa_store`, `qa_admin`) on the one environment; no demo business data this sprint.
- **To confirm with PM (non-blocking):** that frontend lint/type-check/Vitest as local *build gates* are within REQ-009 (ADR-018); `AUTO_ROLLBACK=true` default for this single environment (ADR-015); `LETSENCRYPT_EMAIL` value from the operator before TASK-014.
