# Architecture Decision Records

Owner: Team Lead. Statuses: `PROPOSED` · `ACCEPTED` · `SUPERSEDED by ADR-NNN` · `REJECTED`.
Major changes need a new ADR, as defined in `agents/team-lead.md` §2. Major business changes also need PM/PO approval.

---

## ADR-001 — Backend follows `DRF_SKILL.md`
- **Status:** ACCEPTED (2026-09-27)
- **Context:** The user supplied `DRF_SKILL.md` as the backend engineering standard.
- **Decision:** The backend is built in CREATE mode per `DRF_SKILL.md`: structure, split settings, env configuration, common package, JWT, drf-spectacular, Jazzmin, Health API, DRF throttling, pytest ≥ 80% coverage, Docker local/staging/production, deploy templates, and a Makefile. Its §57 validation commands and §58 DoD are part of every backend task's DoD.
- **Consequences:** Deviations need an ADR. The skill is generic, so Flash-specific rules (ADR-005, ADR-006) sit on top of it. The skill's deployment file *locations* are adapted by ADR-012.

## ADR-002 — Monorepo layout
- **Status:** ACCEPTED (2026-09-27)
- **Decision:** A single repository with `backend/`, `frontend/`, `mobile/`, `qa/`, `.ai/`, `flash_business_logic/`. Directory ownership is defined in `.ai/README.md`.
- **Consequences:** Agents have clear, non-overlapping write scopes. One version history covers business docs, contracts and code.

## ADR-003 — Custom User model with role, from the first migration
- **Status:** ACCEPTED (2026-09-27)
- **Context:** Django cannot cleanly swap `AUTH_USER_MODEL` after the first migrations. Flash has 4 roles.
- **Decision:** `users.User(AbstractUser)` plus `role` (CUSTOMER, DRIVER, STORE, ADMIN), created in the foundation sprint before any `migrate`. Profile models are added per feature. The login identifier (`USERNAME_FIELD`) follows BLK-001. Changing it before production is a simple migration.
- **Consequences:** TASK-003 must land before any other app creates FKs to the user.

## ADR-004 — Business-logic sources of truth
- **Status:** ACCEPTED (2026-09-27)
- **Context:** `flash_business_logic/README.md` declares itself the single source of truth. The agent system requires `.ai/business/business-logic.md`.
- **Decision:**
  - `flash_business_logic/` is **canonical**.
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
- **Status:** ACCEPTED (2026-09-27)
- **Decision:**
  - QA's automated tests run against a running backend over HTTP (pytest + httpx) in `qa/api/` and `qa/api/flows/`.
  - Frontend E2E uses Playwright in `qa/e2e/`.
  - Developer unit and API tests stay inside `backend/` and `frontend/`.
- **Consequences:** QA is independent of implementation internals, and QA never needs to edit application code. QA needs seed data. The backend provides a `seed_demo` management command (Backend task), and QA reviews it.

## ADR-008 — Frontend stack (Vue PWA)
- **Status:** PROPOSED (2026-09-27). Waiting on BLK-002.
- **Proposal:** Vue 3 + TypeScript + Vite, Vue Router, Pinia, `vite-plugin-pwa`, Vitest + Vue Test Utils, ESLint + Prettier. Playwright for E2E (QA). One API client that handles the envelope, JWT refresh and error codes. A UI component library is to be chosen in the design task.
- **Open:** Which clients are in the MVP and in which order; whether Store and Admin are part of the same Vue app (role areas) or separate apps; Flutter timing.

## ADR-009 — Python 3.13 runtime via Docker
- **Status:** ACCEPTED (2026-09-27)
- **Context:** `DRF_SKILL.md` requires Python 3.13+. The development machine has 3.12.3.
- **Decision:** Local Docker (`python:3.13-slim`) is the reference runtime for running and testing. Developers may use a local 3.13 venv if installed. Validation evidence must come from 3.13.

## ADR-010 — API paths and versioning
- **Status:** ACCEPTED (2026-09-27)
- **Decision:** Keep the `DRF_SKILL.md` paths (`/api/auth/…`, `/api/health/`, `/api/schema/`) with no URL version prefix for the MVP. Breaking changes after the first client release need a new ADR (a `/api/v2/` or header-based version).

## ADR-011 — Admin and Store surfaces
- **Status:** PROPOSED (2026-09-27). Waiting on BLK-002.
- **Proposal:**
  - Django Admin/Jazzmin serves internal staff operations from Sprint 1, at no extra cost.
  - The Admin MVP dashboard (`04_admin_dashboard/mvp_scope.md`) and the Store app are role areas of the same Vue app, backed by `/api/admin/…` and `/api/store/…`.
- **Alternative:** Build the Admin MVP entirely on Jazzmin, which is quicker but limits UX and custom dashboards.

## ADR-012 — Infrastructure layout and ownership (adapts DRF_SKILL §3, §41–52)
- **Status:** ACCEPTED (2026-09-27)
- **Context:**
  - `DRF_SKILL.md` places `docker/`, `deploy/` and `scripts/` inside `backend/`, and its Makefile mixes dev and deploy targets.
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
  - `DRF_SKILL.md` itself is not edited.

## ADR-013 — Deployment modes, release layout, rollback and migrations
- **Status:** ACCEPTED (2026-09-27). The hosting target and the default mode are pending BLK-011.
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
