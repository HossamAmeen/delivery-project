"""/api/health/ and /api/health/ready/ (FEAT-001 AC4, AC10; FEAT-004 AC7; ADR-015, ADR-017).

The token is sent only in the X-Health-Check-Token header. The `?password=` variant is
exercised exactly once, with a WRONG value, to prove it rejects (TASK-008 technical notes).
A valid `?password=` is never sent: tooling must not put the token in a URL (ADR-015).
Plan: FEAT-001 TC-001-HLT-01..10.
"""

import pytest

from harness.envelope import assert_error, assert_not_in_response, assert_success, check, describe

pytestmark = [pytest.mark.smoke, pytest.mark.regression]

HEADER = "X-Health-Check-Token"
HEALTH_401_MSG = "Invalid health check password."
HEALTH_401_CODE = "HEALTH_TOKEN_INVALID"  # api-contracts § Error codes (TL, TASK-008 review)
WRONG = "qa-deliberately-wrong-token-0000"


def test_health_with_valid_header_token(api, health_token):
    """TC-001-HLT-01"""
    resp = api.get("/api/health/", headers={HEADER: health_token.reveal()})
    data = assert_success(resp, 200)
    check(data == {"status": "healthy"}, f"unexpected data: {describe(resp)}")


@pytest.mark.security
def test_health_without_token_is_401(api):
    """TC-001-HLT-02"""
    assert_error(api.get("/api/health/"), 401, HEALTH_401_CODE, message=HEALTH_401_MSG)


@pytest.mark.security
def test_health_with_wrong_header_token_is_401(api):
    """TC-001-HLT-03"""
    assert_error(api.get("/api/health/", headers={HEADER: WRONG}), 401, HEALTH_401_CODE, message=HEALTH_401_MSG)


@pytest.mark.security
def test_health_with_wrong_query_password_is_401(api):
    """TC-001-HLT-04: the query variant exists (DRF_SKILL) — only ever tested with a wrong value."""
    resp = api.get("/api/health/", params={"password": WRONG})
    assert_error(resp, 401, HEALTH_401_CODE, message=HEALTH_401_MSG)
    check(WRONG not in resp.text, "the submitted password is echoed back in the body")


@pytest.mark.security
def test_health_with_empty_header_is_401(api):
    """TC-001-HLT-05"""
    assert_error(api.get("/api/health/", headers={HEADER: ""}), 401, HEALTH_401_CODE, message=HEALTH_401_MSG)


@pytest.mark.security
def test_health_response_never_contains_the_token(api, health_token):
    """TC-001-HLT-06: body and headers of valid and invalid calls never contain the token."""
    token = health_token.reveal()
    for path in ("/api/health/", "/api/health/ready/", "/api/status/"):
        assert_not_in_response(api.get(path, headers={HEADER: token}), token, "health token")
        assert_not_in_response(api.get(path), token, "health token")


def test_ready_with_valid_token(api, health_token):
    """TC-001-HLT-07 (+ FEAT-001 AC10): database ok, cache ok, celery skipped."""
    resp = api.get("/api/health/ready/", headers={HEADER: health_token.reveal()})
    data = assert_success(resp, 200)
    check(data.get("status") == "ready", f"status must be 'ready': {describe(resp)}")
    checks = data.get("checks")
    check(
        checks == {"database": "ok", "cache": "ok", "celery": "skipped"},
        f"checks must be database=ok, cache=ok, celery=skipped (CELERY_ENABLED=False, ADR-017): {describe(resp)}",
    )


@pytest.mark.security
def test_ready_without_token_is_401(api):
    """TC-001-HLT-08"""
    assert_error(api.get("/api/health/ready/"), 401, HEALTH_401_CODE, message=HEALTH_401_MSG)


@pytest.mark.security
def test_ready_with_wrong_token_is_401(api):
    """TC-001-HLT-09"""
    assert_error(api.get("/api/health/ready/", headers={HEADER: WRONG}), 401, HEALTH_401_CODE, message=HEALTH_401_MSG)


@pytest.mark.security
def test_health_responses_are_not_cacheable(api, health_token):
    """TC-001-HLT-10: /api/health/ and /ready/ carry Cache-Control: no-store (contract note)."""
    for path in ("/api/health/", "/api/health/ready/"):
        for headers in ({HEADER: health_token.reveal()}, {}):
            resp = api.get(path, headers=headers)
            check("no-store" in resp.headers.get("cache-control", ""), f"{path} without Cache-Control: no-store: {describe(resp)}")
