"""GET /api/users/me/ per role (FEAT-001 AC6; api-contracts § Identity).

Plan: FEAT-001 TC-001-ME-01..04.
"""

import pytest

from harness.config import ROLES
from harness.envelope import assert_error, assert_success, check, describe

pytestmark = [pytest.mark.regression, pytest.mark.security]

REQUIRED_KEYS = {"id", "username", "role", "is_staff"}
FORBIDDEN_KEYS = {"password", "password_hash", "last_login_ip", "is_superuser_secret"}


@pytest.mark.smoke
@pytest.mark.parametrize("role", ROLES)
def test_each_role_authenticates_and_reads_me(api, auth_headers, creds, role):
    """TC-001-ME-01: every QA role logs in with username + password and gets the right role."""
    resp = api.get("/api/users/me/", headers=auth_headers(role))
    data = assert_success(resp, 200)
    check(REQUIRED_KEYS <= set(data), f"missing keys {REQUIRED_KEYS - set(data)}: {describe(resp)}")
    check(not (FORBIDDEN_KEYS & set(data)), f"sensitive keys exposed: {describe(resp)}")
    check(data["username"] == creds(role).username, f"username mismatch: {describe(resp)}")
    check(data["role"] == role, f"expected role {role}: {describe(resp)}")
    check(isinstance(data["id"], int), f"id must be an integer: {describe(resp)}")
    check(data["is_staff"] is (role == "ADMIN"), f"is_staff must be {role == 'ADMIN'} for {role}: {describe(resp)}")


def test_me_without_credentials(api):
    """TC-001-ME-02"""
    assert_error(api.get("/api/users/me/"), 401, "NOT_AUTHENTICATED")


# "Bearer " (trailing space) is not sendable: httpx/h11 reject a header value with trailing
# whitespace (RFC 9110 field-value), so it cannot reach the server; "Bearer" covers the case.
@pytest.mark.parametrize("header", ["Bearer", "Token abc", "Basic cWE6cWE="])
def test_me_with_malformed_authorization_header(api, header):
    """TC-001-ME-03: malformed/foreign schemes -> 401 envelope, never 500."""
    resp = api.get("/api/users/me/", headers={"Authorization": header})
    assert_error(resp, 401, require_code=True)


def test_role_is_read_only(api, auth_headers):
    """TC-001-ME-04: a customer cannot change their role through the API."""
    headers = auth_headers("CUSTOMER")
    for method in ("PATCH", "PUT"):
        resp = api.request(method, "/api/users/me/", headers=headers, json={"role": "ADMIN", "is_staff": True})
        check(resp.status_code in (200, 400, 403, 405), f"unexpected status on {method}: {describe(resp)}")
    after = assert_success(api.get("/api/users/me/", headers=headers))
    check(after["role"] == "CUSTOMER" and after["is_staff"] is False, "role/is_staff changed through the API")
