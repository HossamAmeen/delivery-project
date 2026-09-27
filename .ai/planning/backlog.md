# Product Backlog

Owner: PM. Ordered by priority, then dependency. Template: `.ai/templates/feature.md`.
Priority scale: P0 = the product cannot work without it · P1 = MVP · P2 = soon after the MVP · P3 = later.

Features without an explicit Infrastructure line are **Infrastructure: N/A unless the TL's design adds deploy/runtime needs** (a new service, worker, env var, port or path). In that case the TL adds an Infrastructure task in the same sprint.

---

### FEAT-001 — Backend Platform Foundation
- **Priority:** P0 · **Status:** TODO · **Sprint:** sprint-01
- **Business refs:** REQ-001, REQ-002, REQ-006, REQ-009, REQ-011 (login identifier); `DRF_SKILL.md` §4 (CREATE mode); ADR-003
- **User value:** Every later feature is built on a secure, tested, documented and containerized backend.
- **Work needed:** Backend: Required · Frontend: N/A (no UI; FEAT-003 consumes it) · QA: Required (on the server, REQ-009) · Infrastructure: Required (server runtime via FEAT-004; backend CI deferred on BLK-012)
- **Dependencies:** none for the build. Acceptance evidence needs the FEAT-004 server deployment (REQ-009).
- **Acceptance criteria:**
  1. The backend runs on Python 3.13 and starts with a single documented command. The reference runtime is the deployed server (REQ-009). A local Docker setup is optional developer tooling and is not an acceptance gate (PO: the local machine is for building only).
  2. Configuration comes only from environment variables, and `.env.example` documents every variable.
  3. Every API error (validation, 401, 403, 404, 429, unexpected) returns the standard error envelope.
  4. `GET /api/health/` returns healthy with a valid token and is rejected without one or with a wrong one. The token is never exposed.
  5. Anonymous, authenticated, auth-endpoint and health requests are rate-limited with env-configurable limits, and a throttled request returns 429 in the standard envelope.
  6. JWT access/refresh endpoints work for a user of the custom User model that carries one of the four roles. Users log in with **username + password** (BLK-001 RESOLVED). A username is unique, and a wrong username or password is rejected without revealing which one was wrong.
  7. The OpenAPI schema and docs are available and document 429.
  8. The Django Admin (Jazzmin) is reachable only by staff.
  9. The test suite passes with ≥ 80% coverage, and `check` / `makemigrations --check` pass. **Run on the server** under Python 3.13, with the evidence recorded (REQ-009).
  10. The app starts and runs with `CELERY_ENABLED=False` and no Redis. This is the deployed configuration (BLK-011).
  11. ~~Backend CI~~ **Moved out (2026-09-27):** git init is done, but BLK-012 (provider/remote) is still open. The criterion moves to the FEAT-004 deferred criteria and does not block FEAT-001 acceptance.
- **Open questions:** none. BLK-001 was resolved 2026-09-27.

### FEAT-002 — Identity & Accounts
- **Priority:** P0 · **Status:** BACKLOG · **Sprint:** sprint-02 (target)
- **Business refs:** REQ-010–014; `00_core/02_roles_and_permissions.md`
- **User value:** Customers register and log in; stores, drivers and admins log in; everyone sees their own profile.
- **Work needed:** Backend: Required · Frontend: Required (login/register/profile screens) · QA: Required
- **Dependencies:** FEAT-001, FEAT-003
- **Acceptance criteria:** Defined when BLK-007 is resolved. At minimum: username + password login works for every role (BLK-001 RESOLVED), and a user can read only their own profile.
- **Open questions:** BLK-007 (onboarding, email/phone collection and verification)

### FEAT-003 — Frontend Foundation (Vue PWA)
- **Priority:** P0 · **Status:** TODO · **Sprint:** sprint-01 (unconditional since BLK-002 was RESOLVED on 2026-09-27)
- **Business refs:** REQ-001, REQ-037; `01_customer_app/user_flow.md` (UI states); `06_brand/`
- **User value:** A consistent, installable client shell that every screen is built on.
- **Work needed:** Backend: N/A (consumes FEAT-001 contracts) · Frontend: Required · QA: Required (against the deployed web domain, REQ-009) · Infrastructure: Required (static build served by nginx at `WEB_DOMAIN` via FEAT-004; `frontend.yml` CI deferred on BLK-012; no Docker on the server)
- **Dependencies:** FEAT-001 contracts (APPROVED); FEAT-004 for deployment. BLK-002 RESOLVED.
- **Acceptance criteria:**
  1. The PWA builds, installs and runs on mobile and desktop widths.
  2. One API client handles the standard envelope, 401 (refresh once, then logout), 403, 404 and 429 consistently.
  3. Reusable loading, empty, error and unavailable state components exist.
  4. Role-area routing skeleton for the MVP clients.
  5. Lint, type-check, unit tests and build pass.
  6. The PWA is served over HTTPS at `https://delivery.hossam-ameen.online` and calls the API at `https://api.delivery.hossam-ameen.online` (the API base URL comes from configuration, not hardcoded). A deep link to a client route loads the app, not a 404.
- **Scope note:** Login/registration screens stay in FEAT-002. Any login form built here uses username + password (BLK-001).
- **Open questions:** BLK-009 (i18n/RTL). ADR-011 (Store/Admin as role areas) is the TL's call.

### FEAT-004 — Deployment & Environments
- **Priority:** P0 · **Status:** TODO · **Sprint:** sprint-01 (pulled in 2026-09-27 on PO instruction). CI/CD is deferred until BLK-012. Production go-live readiness is reviewed in sprint-09.
- **Business refs:** REQ-002, REQ-008, REQ-009; BLK-011 (RESOLVED); `DRF_SKILL.md` §41–53, §70–74; ADR-012, ADR-013, ADR-014
- **User value:** The PO can see and use Flash on real HTTPS domains now, and every later feature ships to the same server safely, repeatably and reversibly, without harming the co-hosted dental-clinic app.
- **Target (BLK-011):** one shared GCP VPS (Ubuntu 24.04, `34.123.215.195`, SSH `hossam`, key path `~/.ssh/id_ed25519`), 2 vCPU / 3.8 GB RAM / no swap / about 13 GB free. `DEPLOYMENT_MODE=systemd`, no Docker. SQLite, no Redis. nginx 1.24 + certbot. `API_DOMAIN=api.delivery.hossam-ameen.online`, `WEB_DOMAIN=delivery.hossam-ameen.online`. Backend on `127.0.0.1:8010` (proposed; the TL confirms). One environment (production-like "staging"). Operator-triggered deploys only.
- **Work needed:** Backend: Required (production settings for SQLite/no-Redis, trusted proxy/HTTPS headers, static/media paths, allowed hosts/CORS for the two domains) · Frontend: Required (static build contract, API base URL from `VITE_*` env) · QA: Required (**on the server**: post-deploy smoke, health, rollback verification, dental non-interference check) · **Infrastructure: Required (owner)**
- **Dependencies:** FEAT-001 (a deployable backend), FEAT-003 (a deployable PWA build). BLK-011 RESOLVED. BLK-012 affects only the deferred CI criterion.
- **Acceptance criteria (sprint-01):**
  1. `DEPLOYMENT_MODE` comes from `.env` (value `systemd` for this server). No script hardcodes the mode, host, domains, ports, paths or service names.
  2. `make deploy`, run by the operator from the local machine, deploys backend and frontend over SSH: load and validate env → sync the release → install/build → back up the SQLite database → migrate → switch → restart → health check → report status. A deploy that fails its health check is reported as failed and does not leave the site broken.
  3. `make restart [backend|frontend|all]`, `make migrate`, `make health` and `make rollback` work against the server.
  4. The backend runs under Python 3.13 on the server (provisioning per a TL ADR, e.g. `uv`), as a systemd service bound to `127.0.0.1` only (port 8010 unless the TL records otherwise). It restarts automatically after a crash or reboot.
  5. nginx site configs and the systemd unit are generated from templates and validate (`nginx -t`) before reload. `https://api.delivery.hossam-ameen.online` serves the API, and `https://delivery.hossam-ameen.online` serves the PWA.
  6. Both domains have valid Let's Encrypt certificates, HTTP redirects to HTTPS, and certificate renewal is covered by the existing certbot renewal.
  7. The health check uses the real `/api/health/` and `/api/health/ready/` endpoints with the header token, plus the frontend root and nginx. Both health endpoints are green on the deployed instance, and the health token is never printed or logged.
  8. Versioned releases (`current`, `releases/`, `shared/`). The SQLite database, media and `.env` live in `shared/` and survive deploys. `make rollback` restores the previous release (and the pre-deploy database backup when migrations changed it) and passes the health check.
  9. **Non-interference with dental-clinic:** no file under `/srv/dental-clinic`, no dental nginx site, no `dental-clinic-backend.service` and nothing on port 8000 is modified. The dental sites respond the same before and after a Flash deploy and rollback (checked by QA). Flash has its own nginx site files, service name, deploy path and port.
  10. The deploy fits the server's resources (3.8 GB RAM, no swap, about 13 GB free disk). Heavy build steps must not destabilize the shared server, and old releases/backups are pruned to a documented retention.
  11. No secrets in the repo, templates, scripts or logs. The server `.env` is created from `.env.example` and is readable only by the deploy user/service.
  12. `deploy/README.md` covers the server requirements, SSH setup, env variables, systemd mode, nginx/TLS, all commands, health, rollback, the dental co-hosting rules and troubleshooting.
  13. QA runs its smoke/health suite and the backend test suite **on the server** against the deployed instance, and produces a QA report with verdict PASS and evidence. The TL has reviewed it.
- **Deferred criteria (not in sprint-01):**
  - CI (backend, frontend and deploy pipelines: lint → test → build → security) and backend CI (from FEAT-001 AC11). Needs BLK-012 (provider/remote).
  - Docker deployment mode and a separate production environment. PO: one environment for now, no Docker on this server.
  - PostgreSQL and Redis. PO: SQLite and no Redis for now. Revisit before load-bearing features (assignment concurrency, Celery/notifications).
- **Open questions:** BLK-012 (for the deferred CI only)

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
- **Dependencies:** FEAT-008–011; ADR-011 (surface inside the Vue PWA; BLK-002 RESOLVED)

### FEAT-016 — Audit Trail
- **Priority:** P1 · **Status:** BACKLOG · **Sprint:** sprint-03
- **Business refs:** REQ-004; `00_core/09`
- **Work needed:** Backend (`audit` app + service) · Frontend: N/A until FEAT-015 · QA
- **Dependencies:** FEAT-002

### FEAT-017 — Flutter App (Customer & Driver)
- **Priority:** P2 · **Status:** BACKLOG · **Sprint:** — (after the MVP, per PO decision BLK-002 on 2026-09-27)
- **Dependencies:** MVP API stable
