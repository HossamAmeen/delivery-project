# API Contracts

Owner: Team Lead. Frontend work may start only against contracts marked `APPROVED` or `ACTIVE`.
Contract status values:
- `DRAFT`: being designed
- `APPROVED`: TL approved; implementation may start on both sides
- `ACTIVE`: implemented, and matches OpenAPI
- `DEPRECATED`

The live OpenAPI (`/api/schema/`) must match this file. If they disagree, that is a bug.

## 1. Global conventions

### 1.1 Transport and auth
- JSON over HTTPS, UTF-8.
- Auth header: `Authorization: Bearer <access>` (simplejwt). Refresh through `/api/auth/token/refresh/`.
- No URL versioning for the MVP (ADR-010). Paths follow `docs/standards/DRF_SKILL.md`.
- Trailing slash: required (Django default).
- **Cross-origin (ADR-008):** the PWA (`https://${WEB_DOMAIN}`) and the API are different origins. The API allows exactly `CORS_ALLOWED_ORIGINS=https://${WEB_DOMAIN}` (django-cors-headers), without credentials (no cookies; the client sends `credentials: 'omit'`), and **exposes `Retry-After`** (`CORS_EXPOSE_HEADERS = ["Retry-After"]`, a fixed setting, not an env var) so the browser can read the wait time on a cross-origin 429. Added 2026-09-27 (TASK-007 review); implemented in `backend/config/settings/base.py` and covered by `backend/tests/test_settings.py`.

### 1.2 Response envelope (DRF_SKILL §19)
Success:
```json
{ "success": true, "message": "Operation completed successfully.", "data": { } }
```
Error (every 4xx/5xx, produced by `common/exception_handler.py`):
```json
{ "success": false, "message": "Validation failed.", "errors": { "field": ["This field is required."] } }
```
- Non-field errors go under `errors.non_field_errors`.
- Every error that is not a field validation error carries `errors.code` (see § Error codes introduced by the Foundation), for example 401 `NOT_AUTHENTICATED`, 429 `THROTTLED`. A 400 with field errors may omit it.
- Business-rule violations return 400 or 409, with `errors.code`, a stable machine code such as `INVALID_TRANSITION` or `PRODUCT_UNAVAILABLE`. Clients branch on `code`, never on `message`.

### 1.3 Pagination (collection endpoints)
```json
{ "success": true, "message": "…", "data": { "count": 120, "next": "…?page=3", "previous": "…?page=1", "results": [ ] } }
```
Query parameters: `page`, `page_size` (maximum defined in settings).

### 1.4 Status codes
| Code | Meaning |
|---|---|
| 200 / 201 / 204 | success |
| 400 | validation |
| 401 | unauthenticated |
| 403 | authenticated but role not allowed |
| 404 | not found **or not visible to this actor** |
| 409 | state conflict (invalid transition, duplicate) |
| 429 | rate limited |
| 500 | generic message only |

### 1.5 Data conventions
- Money: `{"amount": "125.50", "currency": "<ISO 4217>"}` or string fields plus an order-level `currency`. The final shape is fixed when BLK-003/BLK-009 are resolved. **Never numbers.**
- Timestamps are ISO 8601 with a timezone (UTC in the API).
- Enums are UPPER_SNAKE strings, the same as the backend enum (for example `READY_FOR_PICKUP`).
- Order resources include `allowed_transitions: ["PREPARING", "CANCELLED"]` for the requesting actor.
- Mutating endpoints that are unsafe to retry accept an `Idempotency-Key` header.

### 1.6 Rate limits (DRF_SKILL §61–83)
Scopes are `anon`, `user`, `auth`, `sensitive` and `health`, all configured from `.env`. Every endpoint may return 429 and documents it.

## 2. Contract registry

### Foundation (FEAT-001), status: ACTIVE (2026-09-28: implemented, QA PASS incl. the BUG-001 re-test, matches OpenAPI; history: revised 2026-09-27: ADR-015, ADR-019; error codes and health bodies fixed in the TASK-002/004 review)
Base URL on the server: `https://api.delivery.hossam-ameen.online` (ADR-015). All JSON responses below are enveloped (§1.2) unless marked "raw".

| Method | Path | Auth | Throttle | Request | Response `data` | Errors |
|---|---|---|---|---|---|---|
| GET | `/api/status/` | none (public, browser-safe; ADR-019) | health | — | `{"status":"ok"}` | 429 |
| GET | `/api/health/` | Header `X-Health-Check-Token` (preferred) **or** `?password=` (supported for DRF_SKILL compatibility; scripts and QA must use the header, ADR-015) | health | — | `{"status":"healthy"}` | 401 `{"success":false,"message":"Invalid health check password.","errors":{"code":"HEALTH_TOKEN_INVALID"}}` (also when missing), 429 |
| GET | `/api/health/ready/` | same | health | — | `{"status":"ready","checks":{"database":"ok","cache":"ok","celery":"skipped"}}` | 401 `HEALTH_TOKEN_INVALID`, 503 `{"success":false,"message":"Service not ready.","errors":{"code":"SERVICE_NOT_READY","checks":{"database":"ok","cache":"error","celery":"skipped"}}}` (names only, no internals), 429 |
| GET | `/api/schema/` | development: none · production (`API_DOCS_PUBLIC=False`): **staff** user (JWT bearer or admin session) (ADR-019) | anon / user | — | OpenAPI 3 (**raw**, not enveloped) | 401 `NOT_AUTHENTICATED`, 403 `PERMISSION_DENIED` (both as the JSON error envelope, even though success is YAML/JSON/HTML), 429 |
| GET | `/api/docs/`, `/api/redoc/` | same as schema | anon / user | — | HTML (raw) | 401, 403, 429 |
| GET | `/admin/` | Django session, **staff only** (Jazzmin) | — | — | HTML | redirect to admin login for non-staff |

Notes:
- The health token is compared in constant time and never appears in responses, headers or logs.
- `/api/health/` and `/api/health/ready/` responses carry `Cache-Control: no-store`.
- Throttle scopes vs. permissions: DRF checks authentication and permissions **before** throttles, so a request rejected with 401/403 is not counted. In sprint-01 no public endpoint uses the `anon` scope (status/health use `health`, login/refresh use `auth`, docs are staff-only in production); the `anon` scope is proven by the backend suite on the server (see FEAT-001 AC5 note in TASK-008's review).
- `celery` is `"skipped"` whenever `CELERY_ENABLED=False` (the server configuration, ADR-017).

### Identity (FEAT-001 foundation), status: ACTIVE (2026-09-28: implemented, QA PASS in TASK-009, matches OpenAPI; BLK-001 RESOLVED: username + password)
| Method | Path | Auth | Throttle | Request | Response `data` | Errors |
|---|---|---|---|---|---|---|
| POST | `/api/auth/token/` | none | auth | `{"username": "string", "password": "string"}` | `{"access": "<jwt>", "refresh": "<jwt>"}` | 400 validation (missing field → `errors.<field>`), 401 `{"success":false,"message":"Invalid username or password.","errors":{"code":"INVALID_CREDENTIALS"}}` (same response for unknown user, wrong password **and inactive user**: never reveals which), 429 |
| POST | `/api/auth/token/refresh/` | none | auth | `{"refresh": "<jwt>"}` | `{"access": "<jwt>"}` (no rotation in the MVP: `JWT_ROTATE_REFRESH_TOKENS=False`) | 400, 401 `{"success":false,"message":"Token is invalid or expired.","errors":{"code":"TOKEN_INVALID"}}`, 429 |
| GET | `/api/users/me/` | Bearer | user | — | `{"id": 1, "username": "qa_customer", "role": "CUSTOMER", "is_staff": false}` | 401 `{"success":false,"message":"Authentication credentials were not provided.","errors":{"code":"NOT_AUTHENTICATED"}}`, 401 `TOKEN_INVALID`, 429 |

Rules:
- `username` is unique across all users and roles (Django `USERNAME_FIELD="username"`, AbstractUser validators). Login is case-sensitive, as in Django's default.
- `role` is one of `CUSTOMER`, `DRIVER`, `STORE`, `ADMIN`. It is read-only through every API.
- Token lifetimes come from `JWT_ACCESS_TOKEN_LIFETIME_MINUTES` (default 30) and `JWT_REFRESH_TOKEN_LIFETIME_DAYS` (default 7).
- `/api/users/me/` is the minimal identity read needed by the PWA; profile fields (email, phone, addresses) are FEAT-002 / BLK-007 and will be **added** (non-breaking) there.
- Client behavior (FEAT-003; refined 2026-09-27, TASK-007 review): on 401 from a Bearer call, refresh once with the stored refresh token (concurrent 401s share one refresh) and retry once.
  - Refresh **rejected** (`/api/auth/token/refresh/` answers 400 or 401, or no refresh token is stored), or the retried call is still 401 → log out (clear both tokens) and go to `/login`.
  - Refresh **not answered** (network error, 5xx, 429) → the request fails with that error and the session is **kept**, so a temporary outage or rate limit does not sign the user out.
  - Logout is client-side only in the MVP: there is no logout/blacklist endpoint, so a refresh token stays valid on the server until it expires (`JWT_REFRESH_TOKEN_LIFETIME_DAYS`). Known limitation of ADR-008.

### Error codes introduced by the Foundation
| `errors.code` | HTTP | Meaning |
|---|---|---|
| `INVALID_CREDENTIALS` | 401 | username/password wrong or user inactive |
| `TOKEN_INVALID` | 401 | access/refresh token invalid or expired |
| `NOT_AUTHENTICATED` | 401 | no credentials |
| `PERMISSION_DENIED` | 403 | role/staff not allowed |
| `NOT_FOUND` | 404 | not found or not visible |
| `METHOD_NOT_ALLOWED` | 405 | |
| `VALIDATION_ERROR` | 400 | set only when there are no field errors (field errors stay as `errors.<field>`) |
| `THROTTLED` | 429 | message `Request rate limit exceeded.`, `Retry-After` header kept |
| `SERVER_ERROR` | 500 | generic message only (`An unexpected error occurred.`); every 5xx `APIException` is mapped to it too |
| `PARSE_ERROR` | 400 | malformed request body (e.g. invalid JSON) |
| `NOT_ACCEPTABLE` | 406 | `Accept` header cannot be satisfied |
| `UNSUPPORTED_MEDIA_TYPE` | 415 | request `Content-Type` not supported |
| `CONFLICT` | 409 | default code of `BusinessConflictError`; features pass their own specific code (e.g. `INVALID_TRANSITION`) and must list it here |
| `APPLICATION_ERROR` | 400 | fallback of the `ApplicationError` base class only; features always pass a specific code |
| `HEALTH_TOKEN_INVALID` | 401 | `/api/health/*`: missing or wrong health token (`Invalid health check password.`) |
| `SERVICE_NOT_READY` | 503 | `/api/health/ready/`: at least one check failed; `errors.checks` names each check |

Codes added 2026-09-27 in the TASK-002/004 review (additive). Any other 4xx `APIException` falls back to its DRF `default_code` upper-cased; such a code is not part of the contract until it is listed here. New codes are added to this table in the same change that introduces them.

Registration, addresses, catalog, orders, driver and admin contracts are added by the TL in the design of the feature that introduces them.
