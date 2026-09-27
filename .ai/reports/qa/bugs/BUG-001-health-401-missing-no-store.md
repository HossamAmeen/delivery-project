# Bug Report

## Bug ID

BUG-001

## Feature

FEAT-001 — Backend Platform Foundation (related task: TASK-004)

## Severity

Low

<!-- A contract deviation with no functional or security impact today. A 401 body holds no
     secret, and nginx/the browsers do not cache these responses by default. It is still a
     broken contract statement, found by TC-001-HLT-10. -->

## Business Rule Violated

`api-contracts.md` § Foundation, Notes: "`/api/health/` and `/api/health/ready/` responses carry `Cache-Control: no-store`." FEAT-001 AC4 (health endpoint behaviour). Test plan TC-001-HLT-10.

## Steps to Reproduce

1. `GET https://api.delivery.hossam-ameen.online/api/health/` with **no** `X-Health-Check-Token` header, or with a wrong one.
2. Look at the response headers.
3. Repeat for `/api/health/ready/`.

## Expected Result

401 `HEALTH_TOKEN_INVALID` envelope **and** `Cache-Control: no-store`. The contract note covers every response of these two endpoints, not only the successful ones.

## Actual Result

The 401 has no `Cache-Control` header. `no-store` is set only on the 200 responses. In `backend/apps/health/views.py` only the success `Response(...)` objects (lines 69 and 96) pass `headers={"Cache-Control": "no-store"}`. The 401 raised through the exception handler does not get it, and neither does the 503 readiness path, judging by the code: 503 cannot be triggered live.

## Environment

- Live release `20260927-205803` (commit `f85848b`, `REVISION dirty=false`).
- Production settings on the server. Checked from the server through nginx over HTTPS with `make qa-remote`.

## Evidence

- `make qa-remote ARGS="-m 'regression and not e2e'"` → run `20260927-225552-109762`: `1 failed, 104 passed, 1 skipped`. Output in `qa/.results/20260927-225552-109762/output.log`:
  ```
  FAILED api/test_health.py::test_health_responses_are_not_cacheable
  E   AssertionError: /api/health/ without Cache-Control: no-store: GET /api/health/ -> 401; body='{"success":false,"message":"Invalid health check password.","errors":{"code":"HEALTH_TOKEN_INVALID"}}'
  ```
- The same failure appears in the smoke run `20260927-210423-33520`. The valid-token requests in the same test passed (`no-store` present on the 200s).

## Suggested Area

Backend. Suggested fix: set the header for every response of the health views, for example in `finalize_response` or with `never_cache`/a decorator on both views, and cover 401 and 503 in the tests.

## Status

OPEN

## Activity Log
- 2026-09-28 | qa | — → OPEN | filed from TASK-009 (TC-001-HLT-10)
