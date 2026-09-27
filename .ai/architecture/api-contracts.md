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
- No URL versioning for the MVP (ADR-010). Paths follow `DRF_SKILL.md`.
- Trailing slash: required (Django default).

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

### Foundation (FEAT-001), status: APPROVED
| Method | Path | Auth | Throttle | Request | Response `data` | Errors |
|---|---|---|---|---|---|---|
| GET | `/api/health/` | Header `X-Health-Check-Token` (preferred) **or** `?password=` | health | — | `{"status":"healthy"}` | 401 `Invalid health check password.` (also when missing), 429 |
| GET | `/api/health/ready/` | same | health | — | `{"status":"ready","checks":{"database":"ok","cache":"ok","celery":"skipped"}}` | 401, 503 (checks listed, no internals), 429 |
| GET | `/api/schema/` | none (dev) / admin-only in production *(TL to confirm in TASK-004)* | anon | — | OpenAPI 3 (raw, not enveloped) | 429 |
| GET | `/api/docs/`, `/api/redoc/` | same as schema | anon | — | HTML | 429 |

### Identity (FEAT-001 / FEAT-002), status: DRAFT until BLK-001 is resolved
| Method | Path | Auth | Throttle | Request | Response `data` |
|---|---|---|---|---|---|
| POST | `/api/auth/token/` | none | auth | `{<identifier>, "password"}` (identifier per BLK-001) | `{"access","refresh"}` |
| POST | `/api/auth/token/refresh/` | none | auth | `{"refresh"}` | `{"access"}` (+`refresh` if rotation is on) |
| GET | `/api/users/me/` | Bearer | user | — | `{"id","role", …profile fields TBD}` |

Registration, addresses, catalog, orders, driver and admin contracts are added by the TL in the design of the feature that introduces them.
