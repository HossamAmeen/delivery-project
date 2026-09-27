"""GET /api/status/ — public, browser-safe, minimal (ADR-019; FEAT-001 AC4 context, FEAT-003 AC6).

Plan: FEAT-001 TC-001-STAT-01..03.
"""

import pytest

from harness.envelope import assert_success, check, describe

pytestmark = [pytest.mark.smoke, pytest.mark.regression]


def test_status_is_public_and_returns_ok(api):
    """TC-001-STAT-01: no auth needed; success envelope with data == {"status": "ok"}."""
    resp = api.get("/api/status/")
    data = assert_success(resp, 200)
    check(data == {"status": "ok"}, f"data must be exactly {{'status': 'ok'}}: {describe(resp)}")


@pytest.mark.security
def test_status_exposes_no_internals(api):
    """TC-001-STAT-02: no version, hostname, DB or config details (ADR-019)."""
    resp = api.get("/api/status/")
    body = resp.json()
    check(set(body) == {"success", "message", "data"}, f"unexpected top-level keys: {describe(resp)}")
    lowered = resp.text.lower()
    for word in ("version", "hostname", "database", "sqlite", "redis", "celery", "debug", "/srv/"):
        check(word not in lowered, f"/api/status/ exposes {word!r}: {describe(resp)}")


@pytest.mark.security
def test_status_ignores_bearer_garbage(api):
    """TC-001-STAT-03: a public endpoint must not fail because of an invalid Authorization header
    it does not need. Records the behaviour; 200 or 401 TOKEN_INVALID are both contract-safe,
    anything else (5xx) is a defect."""
    resp = api.get("/api/status/", headers={"Authorization": "Bearer not-a-jwt"})
    check(resp.status_code in (200, 401), f"unexpected status: {describe(resp)}")
