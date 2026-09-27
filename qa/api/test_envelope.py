"""Standard error envelope on every error path (FEAT-001 AC3; api-contracts.md §1.2, § Error codes).

429 is covered in test_ratelimit.py (run last). A 500 cannot be triggered safely from outside;
the plan records it as a gap covered by the developer suite audit (TASK-009) plus the
no-internals checks below.
Plan: FEAT-001 TC-001-ENV-01..08.
"""

import pytest

from harness.envelope import assert_error, assert_no_leak, check, describe

pytestmark = [pytest.mark.regression]


def test_400_field_errors_on_token_obtain(auth_api):
    """TC-001-ENV-01: missing fields -> 400, errors.username / errors.password lists."""
    resp = auth_api.obtain_raw(json={})
    assert_error(resp, 400, fields=("username", "password"))


def test_400_malformed_json_is_enveloped_not_500(auth_api):
    """TC-001-ENV-02: a body that is not JSON -> 400 in the envelope with an errors.code."""
    resp = auth_api.obtain_raw(content=b'{"username": "x", ', headers={"Content-Type": "application/json"})
    assert_error(resp, 400, require_code=True)


def test_401_not_authenticated(api):
    """TC-001-ENV-03"""
    assert_error(api.get("/api/users/me/"), 401, "NOT_AUTHENTICATED")


@pytest.mark.security
def test_403_permission_denied_for_non_staff_on_schema(api, auth_headers):
    """TC-001-ENV-04: authenticated but not staff -> 403 PERMISSION_DENIED (ADR-019)."""
    assert_error(api.get("/api/schema/", headers=auth_headers("CUSTOMER")), 403, "PERMISSION_DENIED")


def test_404_unknown_api_route(api):
    """TC-001-ENV-05: an unknown /api/ path -> 404 envelope NOT_FOUND, not an HTML page."""
    resp = api.get("/api/qa-does-not-exist-404/")
    assert_error(resp, 404, "NOT_FOUND")


def test_405_method_not_allowed(api):
    """TC-001-ENV-06: POST on a GET-only endpoint -> 405 METHOD_NOT_ALLOWED."""
    assert_error(api.post("/api/status/", json={}), 405, "METHOD_NOT_ALLOWED")


def test_405_on_token_endpoint_get(auth_api):
    """TC-001-ENV-07: GET on the POST-only token endpoint -> 405 METHOD_NOT_ALLOWED."""
    auth_api.pacer.acquire()
    assert_error(auth_api.client.get("/api/auth/token/"), 405, "METHOD_NOT_ALLOWED")


@pytest.mark.security
def test_error_bodies_leak_no_internals(api):
    """TC-001-ENV-08: DEBUG is off; no traceback, path or settings leak on 404/405 paths."""
    for resp in (
        api.get("/api/qa-does-not-exist-404/"),
        api.get("/qa-not-an-api-path/"),
        api.put("/api/status/", json={"x": 1}),
    ):
        assert_no_leak(resp)
        check("URLconf" not in resp.text, f"Django debug 404 page exposed: {describe(resp)}")
