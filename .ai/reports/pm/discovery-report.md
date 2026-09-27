# Project Discovery Report — Flash

- **Date:** 2026-09-27
- **Prepared by:** Project Manager, with a technical inspection by the Team Lead
- **Purpose:** Initial repository inspection before any implementation (agent system setup, §23)

## 1. Project Overview
**Flash** is a multi-sided delivery platform:
- **Customers** order items from **Stores** (pharmacies, supermarkets, flower shops, restaurants, …).
- The **system automatically assigns** a **Driver**. The driver picks up the order, delivers it, and may collect cash from the customer.
- **Admins** operate the platform.

The defining business rules:
- The driver has **no Accept/Reject** step.
- The backend is the single authority for state, assignment, pricing, fees and permissions.
- Money uses Decimal amounts with per-order snapshots and an idempotent ledger.
- The driver sees the amount to collect, the store amount, the fees and the total **separately**.

The planned product surfaces are: a Customer app, a Driver app, a Store app and an Admin dashboard, delivered through a Vue PWA and later Flutter.

## 2. Technology Stack
| Layer | Status | Source |
|---|---|---|
| Backend | **Defined, not built.** Python 3.13+, Django, DRF, simplejwt, drf-spectacular, Jazzmin, django-environ, dj-database-url, pytest(+cov), ruff. Optional Celery + Redis | `DRF_SKILL.md` |
| Database | SQLite (local), PostgreSQL (staging/production) | `DRF_SKILL.md` §2 |
| Frontend | **Named, not specified.** "Vue PWA" and "Flutter" | `flash_business_logic/README.md` |
| Infrastructure | Docker/Compose per environment, Nginx, systemd templates | `DRF_SKILL.md` §41–52 |
| Push notifications | Firebase (future) | `00_core/08` |

Machine toolchain found:
- Python **3.12.3**, which is below the required 3.13
- Docker and Compose v5.5
- Node 24.3
- git installed
- no Flutter SDK

## 3. Repository Structure (as found)
```
delivery_project/
├── DRF_SKILL.md                       # backend engineering standard (1,758 lines)
├── flash_business_logic/              # 26 business-rule docs + brand
│   ├── 00_core/ (10 files)            # domain, roles, lifecycle, assignment, pricing, ledger, catalog, notifications, audit, terms
│   ├── 01_customer_app/ 02_driver_app/ 03_store_app/ 04_admin_dashboard/
│   ├── 05_cross_app_flows/ (6 files)  # order, assignment, money, cancellation, notification, QA contract
│   └── 06_brand/                      # initial logo
├── flash_business_logic_complete.zip  # byte-identical copy of the folder (verified)
└── 06_brand/                          # duplicate of flash_business_logic/06_brand (logo identical)
```
Created by this setup: `.ai/`, `.claude/agents/`, `CLAUDE.md`.

**The project is not a git repository.**

## 4. Existing Features
**None.** No application code, tests, migrations or configuration exist. This is a greenfield project with documentation only.

## 5. Architecture
Nothing is implemented yet. The target architecture is in `.ai/architecture/architecture.md`, with the decisions in ADR-001 to ADR-011:
- a monorepo
- a DRF backend per `DRF_SKILL.md`, with domain apps `users`, `stores`, `orders`, `assignments`, `payments`, `notifications`, `audit` and the shared `common/` package
- a service-layer order state machine with row locks, history and idempotency
- an append-only ledger
- a `NotificationService` abstraction
- a Vue PWA frontend (proposed)

## 6. Database
Nothing exists yet. The conceptual entities come from `00_core/01`:
- User and the customer/driver profiles, Store, StoreCategory, Product, Address
- Order, OrderItem, OrderStatusHistory, DriverAssignment
- Payment/Collection, fees, Wallet/LedgerEntry
- Notification, AuditLog

Key constraint: a **custom User model is needed before the first migration** (ADR-003).

## 7. APIs
Nothing exists yet. Conventions come from `DRF_SKILL.md`: the standard envelope, JWT, OpenAPI at `/api/schema|docs|redoc/`, a token-protected `/api/health/`, and DRF throttling.
The contract registry has started in `.ai/architecture/api-contracts.md`. Only the foundation endpoints are APPROVED.

## 8. Frontend
Nothing exists yet. The business docs define:
- the screens and flows for each app
- mandatory UI states (loading, empty, error, unavailable)
- the driver money-display rules

Still undecided: which clients are in the MVP, the platform for the store and admin surfaces, and the frontend stack (BLK-002, ADR-008 and ADR-011 are PROPOSED).

## 9. Testing
There is no testing infrastructure yet.
- The backend standard requires pytest, pytest-django and pytest-cov with ≥ 80% coverage, plus mandatory health and rate-limit tests.
- The business side provides a 15-scenario QA contract (`05_cross_app_flows/06_qa_contract.md`).
- QA tests will be black-box in `qa/` (ADR-007).

## 10. Deployment
Nothing exists yet. The standard defines docker local/staging/production, nginx and systemd templates generated from `.env`, deploy scripts with a health check, and a Makefile.
The hosting target, domains and CI platform are unknown (BLK-011).

## 11. Business Logic
The business logic is well structured, consistent across files, and strong on principles: authority, snapshots, idempotency, audit, no accept/reject.
It is **thin on concrete rules**. It uses "recommended", "may" and "according to the business model" where a formula or a matrix is needed.
A digest with a source cited for every rule is in `.ai/business/business-logic.md`, and the requirements catalog is in `.ai/business/requirements.md`. Of the 45 requirements:
- **23 DEFINED**
- **17 PARTIAL**
- **5 BLOCKED**

## 12. Missing Requirements (→ blockers, owner PM/PO)
| Blocker | Missing | Blocks |
|---|---|---|
| BLK-001 | Login identifier / auth method per role | FEAT-002 (partly TASK-003) |
| BLK-002 | MVP client list, platforms, frontend stack | FEAT-003, all UI |
| **BLK-003** | **Fee formula, store/driver amount model, ledger accounts, rounding** | **FEAT-008, FEAT-011 (critical path)** |
| BLK-004 | Payment methods; collection discrepancy procedure | FEAT-010, FEAT-011 |
| BLK-005 | Cancellation/reject/fail matrix, recovery paths, admin overrides | FEAT-008 state table, FEAT-012 |
| BLK-006 | MVP assignment algorithm, availability model, no-driver fallback | FEAT-009 |
| BLK-007 | Onboarding per role, store staff, role multiplicity, visibility, retention | FEAT-002, FEAT-005, FEAT-006 |
| BLK-008 | One store per order, store profile/hours, address/geo format | FEAT-005, FEAT-007, FEAT-008 |
| BLK-009 | Languages/RTL, timezone, currency and precision | Money precision, UI i18n |
| BLK-010 | Notification recipient matrix; Firebase timeline | FEAT-013 |
| BLK-011 | Hosting target, domains, staging, CI | FEAT-004 |

Also noted:
- The lifecycle has snapshots taken "at creation/confirmation" (ambiguous), and assignment starts only at READY_FOR_PICKUP. Both are included in BLK-003 and BLK-006 for confirmation.

## 13. Technical Risks
| # | Risk | Impact | Mitigation |
|---|---|---|---|
| R1 | No version control | No reviewable diffs or rollback; the TL review process can't work properly | `git init` plus an initial commit in Sprint 1 (user approval needed) |
| R2 | Python 3.12 locally vs the 3.13+ requirement | Tests pass locally but fail in production, or the reverse | Docker is the reference runtime (ADR-009) |
| R3 | The financial model is undefined (BLK-003/004) | The critical path stalls at Sprint 4; there is a risk of an invented fee logic | Escalate now, and ask for worked examples |
| R4 | Custom user model timing | A painful migration if it is added late | ADR-003: include it in the foundation |
| R5 | Concurrency (assignment, completion, ledger) | Double assignment, duplicate money | ADR-006; DB constraints; concurrency tests required by QA |
| R6 | Business rules could be duplicated in the clients | Inconsistent behavior across Vue, Flutter and Admin | `allowed_transitions` from the API; frontend rules; QA cross-client checks |
| R7 | Admin scope creep ("not an ERP") | Schedule | MVP scope is fixed by `mvp_scope.md` |
| R8 | Duplicated assets (zip, `06_brand`) | Drift | Keep `flash_business_logic/` as canonical; remove the duplicates only with the user's approval |
| R9 | The health endpoint uses a query-string password | The secret leaks into access logs | Accept the `X-Health-Check-Token` header (preferred) as well as the query parameter; never log it |

## 14. Recommended Sprint 1
**Goal:** Deliver the backend platform foundation (DRF_SKILL CREATE mode), with independent QA verification. Frontend scaffolding joins only if BLK-002 is resolved by 2026-09-30.

- **FEAT-001 Backend Platform Foundation:**
  - structure, settings, env, common infrastructure
  - custom User and role, JWT, OpenAPI, Jazzmin, Health API, throttling
  - optional Celery toggle, pytest, local Docker, Makefile
- **FEAT-003 Frontend Foundation:** conditional on BLK-002.
- **QA:** the test strategy, the black-box harness in `qa/`, and verification of FEAT-001.
- **Setup action:** initialize git.
- **In parallel, PM work:** get BLK-001, BLK-002, BLK-007 and BLK-011 resolved for Sprint 2, and start BLK-003 now because it gates the critical path.

Not in Sprint 1: any domain feature (catalog, orders, assignment, money), and staging/production deployment.

---

## Addendum — 2026-09-27: Infrastructure / DevOps agent

The agent specification added a seventh agent (Infrastructure/DevOps, §25–49). Deployment findings from the same inspection:

- **Existing deployment infrastructure:** none. No `deploy/`, Dockerfiles, compose files, Nginx, systemd, CI workflows or Makefile exist.
- **Git provider:** none. The directory is not a repository → **BLK-012** (the provider decides the CI format, secrets and registry).
- **Target environment:** unknown → **BLK-011** has been extended. It now covers the default `DEPLOYMENT_MODE` per environment, SSH access, domains and TLS, managed vs self-hosted DB/Redis, and the `AUTO_DEPLOY` policy.
- **Conflicts resolved by ADR:**
  - **ADR-012:** `DRF_SKILL.md` puts `docker/` and `deploy/` inside `backend/`. The spec wants a repo-root `deploy/` that serves both backend and frontend. Deployment moves to the root and is owned by Infrastructure, and the skill's deployment requirements still apply.
  - **Env split (ADR-012):** a root `.env.example` for deployment variables, and `backend/.env.example` for application variables. They are merged in `shared/.env` on servers.
  - **ADR-013:** the dual `DEPLOYMENT_MODE=docker|systemd` command set, versioned releases, and image/symlink rollback. **Migrations are forward-only and must stay backward-compatible with the previous release**, because rollback never reverses migrations.
  - **Frontend:** it is a static Vite build served by Nginx in both modes. A frontend systemd unit is created only if a server-side frontend process is ever added.
- **Plan changes:**
  - TASK-006 (local Docker) was reassigned from Backend to Infrastructure.
  - TASK-011 (backend CI) was added to Sprint 1, blocked on BLK-012.
  - FEAT-004 was rewritten to cover the full infrastructure definition of done and raised to P0 for Sprint 2.
- **New risk R10:** deployment cannot be "tested in the target environment" (infra DoD) until BLK-011 provides a server. Until then, validation is limited to CI, rendered-config checks and `--dry-run` in both modes, and every report must say so explicitly.
