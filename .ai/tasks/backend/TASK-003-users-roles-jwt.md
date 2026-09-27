# Task

## ID
TASK-003

## Title
Custom User model, roles, JWT authentication & role permissions

## Feature
FEAT-001 — Backend Platform Foundation

## Description
Create `apps/users` with the custom User model and role (username + password login, BLK-001 RESOLVED), register it in Jazzmin admin, expose simplejwt token/refresh with the `auth` throttle scope and `GET /api/users/me/`, provide role permission classes and the `create_role_user` management command used to seed QA users on the server.

## Business Requirement
REQ-010, REQ-011, REQ-003; `00_core/02_roles_and_permissions.md`; business-logic.md §2 (login = username + password for every role, BLK-001 RESOLVED 2026-09-27); ADR-003; DRF_SKILL.md §17–18, §66; FEAT-001 criterion 6; api-contracts.md § Identity (APPROVED)

## Agent
Backend

## Scope (allowed paths)
- `backend/apps/users/**`, `AUTH_USER_MODEL` + JWT sections of settings, auth + users routes in `backend/config/urls.py`

## Dependencies
- TASK-004 (sequencing: shares `config/urls.py` and settings; backend order is TASK-001 → 002 → 005 → 004 → 003)
- BLK-001 — RESOLVED 2026-09-27: username + password

## Acceptance Criteria

- [ ] `users.User(AbstractUser)` + `role` field with `Role` choices CUSTOMER, DRIVER, STORE, ADMIN (UPPER_SNAKE values); `AUTH_USER_MODEL = 'users.User'`; `USERNAME_FIELD = "username"` (Django default, unique, AbstractUser validators); initial migration created.
- [ ] Custom manager supports `create_user`/`create_superuser` (superuser gets role ADMIN, `is_staff=True`). `role` is required on `create_user` (no silent default) — or defaults to CUSTOMER only if written in the plan and approved.
- [ ] Admin registration under Jazzmin (list/search by username, filter by role); admin requires staff.
- [ ] `POST /api/auth/token/` with `{"username","password"}` and `POST /api/auth/token/refresh/` return exactly the shapes in api-contracts.md § Identity, including 401 `INVALID_CREDENTIALS` with the same message for unknown user, wrong password and inactive user; `TOKEN_INVALID` for bad/expired tokens; token lifetimes from env; `JWT_ROTATE_REFRESH_TOKENS=False`; `auth` throttle scope applied to both.
- [ ] `GET /api/users/me/` (Bearer, `user` scope) returns `{id, username, role, is_staff}`; role is read-only everywhere.
- [ ] Role permission classes `IsCustomer`, `IsDriver`, `IsStoreUser`, `IsPlatformAdmin` in `apps/users/permissions.py`.
- [ ] Management command `create_role_user --username <u> --role <ROLE> [--staff] [--superuser] [--update]`: reads the password from the env var `FLASH_NEW_USER_PASSWORD` or from stdin with `--password-stdin` — **never from argv**; idempotent with `--update` (sets password/role on an existing user); never prints the password. Used on the server by `make seed-qa-users` (ADR-018).
- [ ] api-contracts.md Identity rows match the implementation (report any difference to the TL; the TL moves them to ACTIVE after QA).
- [ ] Tests pass on the server with `make test-backend-remote`; total backend coverage ≥ 80%.

## Technical Notes

- No registration endpoint and no profile models (FEAT-002). `/api/users/me/` is only the minimal identity read.
- Role is not user-editable through any API.
- Do not add business rules about which role can log in where — not defined yet (BLK-007).
- Wrap simplejwt serializer errors so the envelope/code in the contract is produced (a custom `TokenObtainPairView` subclass + serializer is fine); do not reveal whether the username exists.
- Username login is case-sensitive (Django default); no normalization beyond Django's.

## Testing Requirements

- Model/manager tests (normalization, uniqueness, superuser role).
- JWT: obtain, refresh, invalid credentials (401 envelope), inactive user.
- `test_auth_endpoint_uses_stricter_throttle`.
- Permission class tests for each role (allow + deny).
- Admin: non-staff redirected/denied.

## Plan Review Required
Yes — authentication architecture; irreversible after first migration. **Pre-approved** against the Acceptance Criteria and api-contracts.md § Identity: write `## Implementation Plan` (model fields, manager, views/serializers, command, tests) and proceed; the TL reviews it with the code. Any deviation (e.g. a role default, a different token shape) needs TL approval before coding.

## Status

QA_IN_PROGRESS

## Activity Log
- 2026-09-27 | team-lead | — → TODO | created from sprint-01 technical plan
- 2026-09-27 | team-lead | TODO → TODO | BLK-001 RESOLVED → username + password; added `/api/users/me/` and `create_role_user` for QA seeding; depends on TASK-004 for sequencing; plan pre-approved
- 2026-09-27 | backend | TODO → IN_PROGRESS | started after TASK-004 code complete; plan written under the pre-approved constraints
- 2026-09-27 | backend | IN_PROGRESS → READY_FOR_REVIEW | implementation + tests done; full server run `make test-backend-remote WORKTREE=1` green (run 20260927-175239-1501198: ruff, format, check, makemigrations, 238 passed, coverage 98.42%)
- 2026-09-27 | team-lead | READY_FOR_REVIEW → REVIEW | code inspection done, decisions recorded; verdict pending the TL's own server validation run (denied by the session permission policy)
- 2026-09-27 | team-lead | REVIEW → READY_FOR_QA | code review APPROVED; TL server run 20260927-204315-12107 at 0a5f845: ruff/format/check/makemigrations PASS, 238 passed, coverage 98.42%
- 2026-09-28 | qa | READY_FOR_QA → QA_IN_PROGRESS | FEAT-001 verification on the server started (TASK-009)
- 2026-09-28 | qa | QA_IN_PROGRESS → QA_IN_PROGRESS | QA verdict PASS ticked; status left for TL final review (.ai/reports/qa/FEAT-001-qa-report.md; server runs 20260927-225552-109762 (API regression), 20260927-225436-108557 (ratelimit), backend audit 20260927-225853-111545)

## Implementation Plan
(backend, 2026-09-27 — follows the Acceptance Criteria and api-contracts.md § Identity; no deviation)

**Model** `apps/users/models.py`: `User(AbstractUser)` + `role = CharField(max_length=16, choices=Role.choices)` with **no default** (required), `Role` TextChoices `CUSTOMER`, `DRIVER`, `STORE`, `ADMIN`; `USERNAME_FIELD="username"` (Django default, unique, AbstractUser validators); DB `CheckConstraint` `role IN (...)`. `AUTH_USER_MODEL="users.User"`; migration `0001_initial` (created before any other app's migrations, ADR-003). Not a `BaseModel` (no soft delete for users in this task; `is_active` covers deactivation).
**Manager** `apps/users/managers.py` `UserManager(django UserManager)`: `create_user(username, email=None, password=None, *, role, **extra)` raises `ValueError` when `role` is missing/invalid (no silent default); `create_superuser` forces `role=ADMIN`, `is_staff=True`, `is_superuser=True` and rejects another role. `createsuperuser` keeps working.
**Auth** simplejwt: `SIMPLE_JWT` lifetimes from `JWT_ACCESS_TOKEN_LIFETIME_MINUTES` / `JWT_REFRESH_TOKEN_LIFETIME_DAYS`, `ROTATE_REFRESH_TOKENS` from `JWT_ROTATE_REFRESH_TOKENS` (default False), `AUTH_HEADER_TYPES=("Bearer",)`; `JWTAuthentication` is the only default authentication class.
**Views/serializers**: `LoginView(TokenObtainPairView)` with `LoginSerializer(TokenObtainPairSerializer)` that turns every authentication failure (unknown user, wrong password, inactive user) into `ApplicationError` 401 `INVALID_CREDENTIALS` "Invalid username or password."; missing fields stay 400 field errors. `RefreshView(TokenRefreshView)`: invalid/expired token → 401 `TOKEN_INVALID` (via the common handler). Both `throttle_classes=[AuthRateThrottle]`, no authentication. `MeView(RetrieveAPIView)` `IsAuthenticated`, default `user` throttle, `MeSerializer` `{id, username, role, is_staff}` all read-only; GET only.
**URLs**: `api/auth/token/`, `api/auth/token/refresh/`, `api/users/me/`.
**Permissions** `apps/users/permissions.py`: `IsCustomer`, `IsDriver`, `IsStoreUser`, `IsPlatformAdmin` (authenticated + active + role).
**Admin**: `UserAdmin(django UserAdmin)` with role in fieldsets/add form, `list_display` username/role/is_staff/is_active, `search_fields` username, `list_filter` role/is_staff/is_superuser/is_active. Staff-only by Django admin.
**Command** `create_role_user --username U --role ROLE [--staff] [--superuser] [--update] [--password-stdin]`: password from stdin (first line) or `FLASH_NEW_USER_PASSWORD`, never argv (no `--password` option exists); validated with Django's password validators; existing user without `--update` → error; with `--update` sets password, role, `is_staff`/`is_superuser` to the given flags (desired state, idempotent); `--superuser` requires `--role ADMIN`; output never contains the password.
**Tests**: models/manager (required role, invalid role, superuser, uniqueness, normalization, constraint), JWT (obtain shape, wrong password / unknown user / inactive → identical 401 body, missing field 400, refresh ok, refresh invalid → TOKEN_INVALID, no rotation), `/me` (ok, no credentials → NOT_AUTHENTICATED, bad token → TOKEN_INVALID, read-only methods → 405), `test_auth_endpoint_uses_stricter_throttle` (token + refresh), permissions allow/deny per role, admin (anonymous and non-staff redirected to login, staff sees the changelist), command (env, stdin, update, errors, no password in output, `--password` rejected).

## Completion Report
- Files changed: `backend/apps/users/{__init__,apps,models,managers,permissions,serializers,views,urls,admin}.py`, `backend/apps/users/migrations/{__init__,0001_initial}.py`, `backend/apps/users/management/commands/create_role_user.py`, `backend/apps/users/tests/{__init__,test_models,test_views,test_permissions,test_admin,test_commands}.py`, `AUTH_USER_MODEL` + JWT sections (and JWT default authentication) in `config/settings/base.py`, auth + users routes in `config/urls.py`.
- Tests added (75): models/manager 15 (each role, role required, unknown role, superuser → ADMIN/staff, superuser with other role / false flags refused, username unique across roles, case-sensitive, NFKC normalization, DB check constraint rejects an invalid role); views 26 (token pair shape, wrong password / unknown user / inactive user → identical 401 `INVALID_CREDENTIALS` body, case-sensitive login, missing field → 400 `errors.<field>`, stale bearer ignored on login, refresh ok without rotation, invalid / expired / access-token-as-refresh → 401 `TOKEN_INVALID`, lifetimes from settings, `/me` shape, no credentials → `NOT_AUTHENTICATED`, bad token and inactive user → `TOKEN_INVALID`, PUT/PATCH/POST/DELETE → 405 and role unchanged, `test_auth_endpoint_uses_stricter_throttle` on token + refresh, failed logins throttled, `/me` user throttle); permissions 17 (allow own role, deny other roles, anonymous, inactive; staff flag alone is not ADMIN); admin 5 (anonymous and non-staff redirected to admin login, superuser changelist with role filter/search, add form has role, Jazzmin 'Flash' branding); command 12 (env password, stdin password + superuser, `--staff`, existing without `--update` refused, `--update` idempotent desired state, `--update` creates a missing user, `--superuser` needs ADMIN, missing/empty password, weak password rejected without echo, invalid role, `--password` on argv rejected; the password never appears in output).
- Validation commands run + results (server, `make test-backend-remote WORKTREE=1`, run `20260927-175239-1501198`, Python 3.13.15, HEAD 8b5dc17 + uncommitted worktree; output in `backend/.remote-results/20260927-175239-1501198/`):
  ```
  ruff-check      PASS   (All checks passed!)
  ruff-format     PASS
  check           PASS   (System check identified no issues)
  makemigrations  PASS   (makemigrations --check --dry-run: No changes detected)
  pytest          PASS   238 passed in 4.67s
  coverage        TOTAL 771 stmts, 7 miss -> 98.42% (gate 80%: reached)
  == exit code: 0
  ```
  Previous run `20260927-175219-1500937` failed 1 test (whitespace-only secret accepted by `require_non_placeholder`); fixed, then the run above passed. Locally (Python 3.12, throwaway venv, static only, no pytest per REQ-009): `ruff check .`, `ruff format --check .`, `manage.py check`, `makemigrations --check --dry-run`, `spectacular --validate --fail-on-warn` all clean.
  Total backend coverage 98.42% (users app 100%).
- Contract/OpenAPI changes: none beyond the contract. `/api/auth/token/`, `/api/auth/token/refresh/`, `/api/users/me/` match api-contracts.md § Identity exactly (messages and codes as written; token data keys `access`/`refresh`, refresh returns `access` only). Note for the TL: simplejwt 5.5 writes the `user_id` claim as a string.
- Implementation notes (within the pre-approved plan): `role` has no default (required on `create_user`, ValueError otherwise); `createsuperuser` works and always yields ADMIN. Admin requires staff (Django default). `create_role_user` is the contract for `make seed-qa-users`: `--username --role [--staff] [--superuser] [--update] [--password-stdin]`, password from stdin (first line) or `FLASH_NEW_USER_PASSWORD`, validated by Django's password validators, never printed; with `--update` the flags describe the desired state (omitting `--staff` removes staff).
- Known limitations / remaining problems: no registration/profile endpoints (FEAT-002, BLK-007). Users are not soft-deletable (`is_active` is the deactivation switch). Role-based login restrictions intentionally absent (BLK-007).

## Review Log
- 2026-09-27 | team-lead | PLAN PRE-APPROVED (conditional) | valid while the plan follows the Acceptance Criteria and api-contracts.md § Identity (username + password)

### Review — 2026-09-27 — team-lead — code (in progress)

**Verdict:** PENDING — not issued yet. Code inspection and the decisions below are done; the TL's own validation run (`make test-backend-remote WORKTREE=1`, which executes the DRF_SKILL §57 commands on the server: `ruff check`, `ruff format --check`, `manage.py check`, `makemigrations --check --dry-run`, `pytest --cov`) was **denied by the session's permission policy** (classified as interfering with the shared server). Per team-lead.md §6 ("do not approve work without running the validation yourself") the verdict waits for that run; Backend's run `20260927-175239-1501198` (238 passed, 98.42 %) is noted but is not the TL's evidence. No blocking defect was found in the inspection.

**Checked so far (inspection):** `LoginSerializer` maps every `AuthenticationFailed` (unknown/wrong/inactive) to one 401 `INVALID_CREDENTIALS`; login/refresh `authentication_classes=[]` + `AuthRateThrottle`; `MeSerializer` read-only `{id, username, role, is_staff}`; `create_role_user` password only from stdin/env, validated, never printed.

**Decisions / follow-ups:**
- simplejwt 5.5 writes `user_id` as a string claim — ACCEPTED (clients never read JWT claims; the PWA uses `/api/users/me/`).
- **QA request (TASK-008): an inactive QA user.** `create_role_user` cannot create or keep an inactive user. Not a defect of this task; created **TASK-016** (Backend, `--inactive` flag, desired-state semantics) to start after this task's verdict, consumed by TASK-013 `seed-qa-users` (`qa_inactive`).

### Review — 2026-09-27 — team-lead — code (final)

**Verdict:** APPROVED

**Checked:** the inspection and decisions of the in-progress review above, plus the TL's own validation run below.
- [x] Scope limited to the task; no business rules invented; authorization order respected where applicable
- [x] API contract matches `api-contracts.md` (Foundation/Identity rows and error codes updated in this review)
- [x] Tests meaningful; validation commands pass on the server; `makemigrations --check` clean (only `users/0001_initial`, non-destructive)
- [x] No hardcoded secrets/domains/ports/paths; complies with `DRF_SKILL.md` and ADR-015/017/019

**Commands run:** `make test-backend-remote REF=0a5f845` (DRF_SKILL §57 on the server, ADR-018), run `20260927-204315-12107`, ref `0a5f845` (`0a5f845768c0`), Python 3.13.15, explicit test env (`shared/.env` not read); results in `backend/.remote-results/20260927-204315-12107/`:
```
ruff-check      PASS
ruff-format     PASS
check           PASS   (manage.py check)
makemigrations  PASS   (makemigrations --check --dry-run)
pytest          PASS   238 passed in 4.94s; junit tests=238 failures=0 errors=0 skipped=0
coverage        TOTAL 771 stmts, 7 miss, 98.42% (gate 80%: reached)
== exit code: 0   (remote)
```
The local wrapper then exited 1 with `deploy/scripts/remote-test.sh: line 1: tmp: unbound variable`. That is a runner defect in the `--ref` path (EXIT trap references a `local` variable; TASK-012 sent back), **not** a test failure: every step reported PASS and the remote exit code was 0.

## QA Log
- 2026-09-28 | qa | PASS | .ai/reports/qa/FEAT-001-qa-report.md; server runs 20260927-225552-109762 (API regression), 20260927-225436-108557 (ratelimit), backend audit 20260927-225853-111545

## Sign-off
- TL final review: ☐
- QA verdict: ☑ PASS (.ai/reports/qa/FEAT-001-qa-report.md; server runs 20260927-225552-109762 (API regression), 20260927-225436-108557 (ratelimit), backend audit 20260927-225853-111545)
- PM acceptance: ☐
