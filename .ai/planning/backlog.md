# Product Backlog

Owner: PM. Ordered by priority, then dependency. Template: `.ai/templates/feature.md`.
Priority scale: P0 = the product cannot work without it · P1 = MVP · P2 = soon after the MVP · P3 = later.

Features without an explicit Infrastructure line are **Infrastructure: N/A unless the TL's design adds deploy/runtime needs** (a new service, worker, env var, port or path). In that case the TL adds an Infrastructure task in the same sprint.

---

### FEAT-001 — Backend Platform Foundation
- **Priority:** P0 · **Status:** TODO · **Sprint:** sprint-01
- **Business refs:** REQ-001, REQ-002, REQ-006; `DRF_SKILL.md` §4 (CREATE mode); ADR-003
- **User value:** Every later feature is built on a secure, tested, documented and containerized backend.
- **Work needed:** Backend: Required · Frontend: N/A (no UI; FEAT-003 consumes it) · QA: Required · Infrastructure: Required (local Docker environment, backend CI)
- **Dependencies:** none (backend CI needs BLK-012)
- **Acceptance criteria:**
  1. The backend runs locally in Docker with a single documented command, and with Python 3.13.
  2. Configuration comes only from environment variables, and `.env.example` documents every variable.
  3. Every API error (validation, 401, 403, 404, 429, unexpected) returns the standard error envelope.
  4. `GET /api/health/` returns healthy with a valid token and is rejected without one or with a wrong one. The token is never exposed.
  5. Anonymous, authenticated, auth-endpoint and health requests are rate-limited with env-configurable limits, and a throttled request returns 429 in the standard envelope.
  6. JWT access/refresh endpoints work for a user of the custom User model that carries one of the four roles.
  7. The OpenAPI schema and docs are available and document 429.
  8. The Django Admin (Jazzmin) is reachable only by staff.
  9. The test suite passes with ≥ 80% coverage, and `check` / `makemigrations --check` pass.
  10. The app starts and runs with `CELERY_ENABLED=False` and no Redis.
  11. Backend CI runs lint, the checks and the tests with the coverage gate on every push/PR. *(Conditional on BLK-012 and git init. If they are unresolved, this criterion moves to FEAT-004 and does not block FEAT-001 acceptance.)*
- **Open questions:** Only the login identifier (BLK-001). It affects TASK-003 but not the rest.

### FEAT-002 — Identity & Accounts
- **Priority:** P0 · **Status:** BACKLOG · **Sprint:** sprint-02 (target)
- **Business refs:** REQ-010–014; `00_core/02_roles_and_permissions.md`
- **User value:** Customers register and log in; stores, drivers and admins log in; everyone sees their own profile.
- **Work needed:** Backend: Required · Frontend: Required (login/register/profile screens) · QA: Required
- **Dependencies:** FEAT-001, FEAT-003
- **Acceptance criteria:** Defined when BLK-001 and BLK-007 are resolved. At minimum, role-based login works and a user can read only their own profile.
- **Open questions:** BLK-001, BLK-007

### FEAT-003 — Frontend Foundation (Vue PWA)
- **Priority:** P0 · **Status:** TODO (conditional) · **Sprint:** sprint-01 if BLK-002 is resolved by 2026-09-30, else sprint-02
- **Business refs:** REQ-001, REQ-037; `01_customer_app/user_flow.md` (UI states); `06_brand/`
- **User value:** A consistent, installable client shell that every screen is built on.
- **Work needed:** Backend: N/A (consumes FEAT-001 contracts) · Frontend: Required · QA: Required · Infrastructure: Required (frontend Dockerfile, `frontend.yml` CI)
- **Dependencies:** FEAT-001 contracts (APPROVED), BLK-002
- **Acceptance criteria:**
  1. The PWA builds, installs and runs on mobile and desktop widths.
  2. One API client handles the standard envelope, 401 (refresh once, then logout), 403, 404 and 429 consistently.
  3. Reusable loading, empty, error and unavailable state components exist.
  4. Role-area routing skeleton for the MVP clients.
  5. Lint, type-check, unit tests and build pass.
- **Open questions:** BLK-002, BLK-009 (i18n/RTL)

### FEAT-004 — Deployment, CI/CD & Environments
- **Priority:** P0 (a deployable staging environment is needed before the first client-facing feature) · **Status:** BACKLOG · **Sprint:** sprint-02 (design + scripts + staging); production readiness in sprint-09
- **Business refs:** REQ-002; `DRF_SKILL.md` §41–53, §70–74; agent spec §25–49; ADR-012, ADR-013, ADR-014
- **User value:** Every accepted feature can be shipped to staging and production safely, repeatably and reversibly.
- **Work needed:** Backend: Required (trusted proxy, production settings verified, static/media paths) · Frontend: Required (static build contract, `VITE_*` env) · QA: Required (post-deploy smoke suite, rollback verification) · **Infrastructure: Required (owner)**
- **Dependencies:** FEAT-001; TASK-011 (backend CI); **BLK-011** (hosting, SSH, domains), **BLK-012** (git provider)
- **Acceptance criteria:**
  1. `DEPLOYMENT_MODE=docker|systemd` in `.env` selects the mode. No script hardcodes it.
  2. `make deploy` deploys over SSH to the configured server: load and validate env → sync the release → install/build → migrate → switch → restart → health check → report status.
  3. `make restart [backend|frontend|all]`, `make migrate`, `make health` and `make rollback` work in both modes, and the user does not need to know the mode.
  4. Nginx and systemd configurations are generated from templates. No domains, ports, paths or service names are hardcoded, and the generated files validate.
  5. The health check uses the real `/api/health/` and `/api/health/ready/` endpoints (with the header token), the frontend root, Nginx and the required services. A deploy fails if it is unhealthy.
  6. Versioned releases (`current`, `releases/`, `shared/`). Rollback restores the previous release or image and passes the health check.
  7. CI: the backend, frontend and deploy pipelines run lint → test → build → security. Staging deploys per `AUTO_DEPLOY`. Production requires approval.
  8. No secrets in the repo, workflows, templates, scripts or logs.
  9. `deploy/README.md` covers the server requirements, SSH setup, env variables, both modes, Nginx, CI/CD, all commands, health, rollback and troubleshooting.
  10. Tested in the target (staging) environment, with the evidence recorded. The TL has reviewed it.
- **Open questions:** BLK-011, BLK-012

### FEAT-005 — Store Profile & Catalog Management
- **Priority:** P0 · **Status:** BACKLOG · **Sprint:** sprint-03
- **Business refs:** REQ-013, REQ-020–024; `00_core/07`, `03_store_app/*`
- **Work needed:** Backend: Required · Frontend: Required (store area) · QA: Required
- **Dependencies:** FEAT-002, FEAT-016; BLK-008 (store fields/hours)
- **Acceptance criteria (draft):**
  1. A store manages only its own categories and products.
  2. Deactivate, reactivate and availability toggling work.
  3. Another store's catalog is inaccessible.
  4. Catalog changes are audited.

### FEAT-006 — Driver Management & Availability
- **Priority:** P0 · **Status:** BACKLOG · **Sprint:** sprint-04/05
- **Business refs:** `00_core/04`, `02_driver_app/*`
- **Work needed:** Backend · Frontend (driver shell, admin driver list) · QA
- **Dependencies:** FEAT-002; BLK-006, BLK-007

### FEAT-007 — Customer Browsing & Addresses
- **Priority:** P0 · **Status:** BACKLOG · **Sprint:** sprint-03
- **Business refs:** REQ-012, REQ-023; `01_customer_app/*`
- **Work needed:** Backend · Frontend · QA
- **Dependencies:** FEAT-005; BLK-008

### FEAT-008 — Ordering & Store Order Processing
- **Priority:** P0 · **Status:** BACKLOG · **Sprint:** sprint-04–05
- **Business refs:** REQ-030–035, REQ-037; `00_core/03`, `00_core/05`, `05_cross_app_flows/01`
- **Work needed:** Backend (order aggregate, snapshots, state machine) · Frontend (cart, review, place, store order handling) · QA (QA contract scenarios 1–5)
- **Dependencies:** FEAT-005, FEAT-007; **BLK-003, BLK-005, BLK-008, BLK-009**

### FEAT-009 — System Driver Assignment
- **Priority:** P0 · **Status:** BACKLOG · **Sprint:** sprint-05
- **Business refs:** REQ-040–042; `00_core/04`, `05_cross_app_flows/02`
- **Work needed:** Backend · Frontend (assigned orders appear; no accept/reject) · QA (scenarios 6–8, concurrency)
- **Dependencies:** FEAT-006, FEAT-008; BLK-006

### FEAT-010 — Driver Delivery Execution
- **Priority:** P0 · **Status:** BACKLOG · **Sprint:** sprint-06
- **Business refs:** REQ-043–044; `02_driver_app/*`
- **Work needed:** Backend · Frontend · QA (scenario 11)
- **Dependencies:** FEAT-009, FEAT-011 (completion records the collection)

### FEAT-011 — Collection, Fees & Ledger
- **Priority:** P0 · **Status:** BACKLOG · **Sprint:** sprint-06
- **Business refs:** REQ-050–055; `00_core/05`, `00_core/06`, `05_cross_app_flows/03`
- **Work needed:** Backend · Frontend (driver 4-amount display, store/admin views) · QA (scenarios 9, 10, 12)
- **Dependencies:** FEAT-008; **BLK-003, BLK-004**

### FEAT-012 — Cancellation, Rejection & Failure
- **Priority:** P1 · **Status:** BACKLOG · **Sprint:** sprint-07
- **Business refs:** REQ-036; `05_cross_app_flows/04`
- **Work needed:** Backend · Frontend · QA (scenario 13)
- **Dependencies:** FEAT-008, FEAT-011; **BLK-005**

### FEAT-013 — Notifications
- **Priority:** P1 · **Status:** BACKLOG · **Sprint:** sprint-07
- **Business refs:** REQ-060–062; `00_core/08`, `05_cross_app_flows/05`
- **Work needed:** Backend · Frontend (in-app notification center) · QA (scenario 14)
- **Dependencies:** FEAT-008; BLK-010

### FEAT-014 — Order Tracking & History
- **Priority:** P1 · **Status:** BACKLOG · **Sprint:** sprint-06
- **Business refs:** REQ-035, REQ-045
- **Work needed:** Backend (customer-relevant history projection) · Frontend · QA
- **Dependencies:** FEAT-008

### FEAT-015 — Admin Dashboard MVP
- **Priority:** P1 · **Status:** BACKLOG · **Sprint:** sprint-08
- **Business refs:** REQ-070–074; `04_admin_dashboard/*`
- **Work needed:** Backend (`/api/admin/…` read APIs) · Frontend (per ADR-011) · QA
- **Dependencies:** FEAT-008–011; BLK-002

### FEAT-016 — Audit Trail
- **Priority:** P1 · **Status:** BACKLOG · **Sprint:** sprint-03
- **Business refs:** REQ-004; `00_core/09`
- **Work needed:** Backend (`audit` app + service) · Frontend: N/A until FEAT-015 · QA
- **Dependencies:** FEAT-002

### FEAT-017 — Flutter App (Customer & Driver)
- **Priority:** P2 · **Status:** BACKLOG · **Sprint:** —
- **Dependencies:** MVP API stable; BLK-002
