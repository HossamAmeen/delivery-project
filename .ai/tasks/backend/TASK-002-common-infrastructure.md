# Task

## ID
TASK-002

## Title
Common infrastructure: base model, soft delete, errors, envelope, pagination, throttling

## Feature
FEAT-001 — Backend Platform Foundation

## Description
Implement `backend/common/` per DRF_SKILL.md §10–13, §19–20, §40, §61–72 and wire it into DRF settings.

## Business Requirement
REQ-002, REQ-006; DRF_SKILL.md §10–13, §19–20, §40, §62–72; FEAT-001 criteria 3, 5

## Agent
Backend

## Scope (allowed paths)
- `backend/common/**`, `backend/tests/**`, DRF section of `backend/config/settings/base.py`

## Dependencies
- TASK-001

## Acceptance Criteria

- [ ] `BaseModel` (created_at, modified_at, deleted_at) with `soft_delete()`/`restore()`; `ActiveManager`, `DeletedManager`, `AllManager`.
- [ ] `ApplicationError` base with `status_code`, `code`, `message`; subclasses for business conflict (409) and validation (400).
- [ ] `custom_exception_handler` returns the standard error envelope for: ValidationError, NotAuthenticated/AuthenticationFailed (401), PermissionDenied (403), Http404/NotFound, Throttled (429, message 'Request rate limit exceeded.', Retry-After header kept), ApplicationError, and unexpected exceptions (500, generic message, no stack trace; exception logged server-side).
- [ ] Success responses follow `{success, message, data}` through one consistent mechanism (renderer or response helper — decide in plan).
- [ ] `StandardPagination` returns `data: {count, next, previous, results}`; page size + max page size from settings.
- [ ] Global throttling configured: Anon + User classes, rates for `anon`, `user`, `auth`, `sensitive`, `health` from env; `AuthRateThrottle`, `SensitiveRateThrottle`, `HealthRateThrottle` in `common/throttling.py`.
- [ ] Coverage of `common/` ≥ 90%.

## Technical Notes

- Error `code` values are the stable client contract (api-contracts.md §1.2) — list them in the plan.
- Throttle tests: override cache to LocMem and clear it per test; override rates to small numbers.
- Do not envelope OpenAPI schema responses.

## Testing Requirements

- Model/manager tests using a test-only concrete model.
- Exception handler: one test per error type incl. 500 path (no internals leaked).
- Pagination shape.
- DRF_SKILL §77 rate-limit tests: `test_api_allows_requests_within_rate_limit`, `test_api_rejects_requests_after_rate_limit`, `test_anonymous_user_uses_anonymous_throttle`, `test_authenticated_user_uses_user_throttle`, `test_sensitive_endpoint_has_stricter_rate_limit` (auth-endpoint test lands in TASK-003).

## Plan Review Required
Yes — sets conventions all endpoints inherit

## Status

TODO

## Activity Log
- 2026-09-27 | team-lead | — → TODO | created from sprint-01 technical plan

## Implementation Plan
(assignee: required before coding — wait for TL APPROVED)

## Completion Report
(assignee, when moving to READY_FOR_REVIEW)
- Files changed:
- Tests added:
- Validation commands run + results:
- Contract/OpenAPI changes:
- Known limitations / remaining problems:

## Review Log

## QA Log

## Sign-off
- TL final review: ☐
- QA verdict: ☐
- PM acceptance: ☐
