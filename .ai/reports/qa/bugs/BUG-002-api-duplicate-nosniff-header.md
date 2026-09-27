# Bug Report

## Bug ID

BUG-002

## Feature

FEAT-004 — Deployment & Environments (related task: TASK-013, nginx `api.conf.template`); observed during FEAT-001 verification (TASK-009)

## Severity

Low

<!-- Hygiene. Browsers use the first value of the combined header (Fetch spec), so the
     nosniff protection works. No functional or security impact. -->

## Business Rule Violated

ADR-015 (nginx API site). Response headers should be emitted once. FEAT-004 AC5 (nginx site configs correct). Found by TC-001-SEC-03.

## Steps to Reproduce

1. `GET https://api.delivery.hossam-ameen.online/api/status/` (any API response proxied to gunicorn).
2. Look at the `X-Content-Type-Options` header.

## Expected Result

A single `X-Content-Type-Options: nosniff`. Set it either in Django (`SECURE_CONTENT_TYPE_NOSNIFF=True`) or in nginx, not both, or hide the upstream copy with `proxy_hide_header`.

## Actual Result

`x-content-type-options: nosniff, nosniff`. Django's `SecurityMiddleware` adds it (`backend/config/settings/base.py:138`), and `deploy/nginx/api.conf.template:39` adds it again with `add_header … always`.

## Environment

Live release `20260927-205803` (commit `f85848b`). Requests from the server through nginx over HTTPS (`make qa-remote`).

## Evidence

Run `20260927-224701-94472` (`qa/.results/20260927-224701-94472/output.log`), full response headers of `GET /api/status/`:
```
'x-frame-options': 'DENY', 'vary': 'origin', 'x-content-type-options': 'nosniff, nosniff', 'referrer-policy': 'same-origin', ... 'strict-transport-security': 'max-age=31536000'
```
QA then changed the test to parse the header as the Fetch spec does (first value), so it passes. This bug tracks the duplication.

## Suggested Area

Infrastructure. Suggested fix: remove `add_header X-Content-Type-Options` from the API site (location `/`, proxied) and keep it for `/static/` and `/media/` only, or add `proxy_hide_header X-Content-Type-Options;`. Then `nginx -t` and reload per ADR-015.

## Status

OPEN

## Activity Log
- 2026-09-28 | qa | — → OPEN | filed from TASK-009 (TC-001-SEC-03)
