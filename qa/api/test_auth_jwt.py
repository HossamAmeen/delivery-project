"""JWT obtain/refresh with username + password (FEAT-001 AC6; api-contracts § Identity; BLK-001).

All calls to the auth endpoints go through the AuthPacer so the functional suite stays under
the `auth` throttle. Plan: FEAT-001 TC-001-JWT-01..16.
"""

import time

import pytest

from harness.envelope import assert_error, assert_success, check, describe
from harness.http import JWT_SHAPE, jwt_alg_none, jwt_claims, jwt_tamper_payload, jwt_tamper_signature, register_tokens

pytestmark = [pytest.mark.regression, pytest.mark.security]

WRONG_PASSWORD = "qa-wrong-password-!-0000"


@pytest.mark.smoke
def test_obtain_returns_access_and_refresh(auth_api, creds):
    """TC-001-JWT-01"""
    c = creds("CUSTOMER")
    resp = auth_api.obtain(c.username, c.password)
    data = assert_success(resp, 200)
    register_tokens(data)
    check(set(data) == {"access", "refresh"}, f"data keys must be access+refresh: {sorted(data)}")
    check(bool(JWT_SHAPE.match(data["access"])) and bool(JWT_SHAPE.match(data["refresh"])), "tokens must be JWS compact")


def test_token_lifetimes_match_configuration(tokens, cfg):
    """TC-001-JWT-02: access 30 min / refresh 7 days by default (env-configurable)."""
    t = tokens("CUSTOMER")
    access, refresh = jwt_claims(t["access"]), jwt_claims(t["refresh"])
    check(abs((access["exp"] - access["iat"]) - cfg.access_lifetime_min * 60) <= 5, "access lifetime differs from JWT_ACCESS_TOKEN_LIFETIME_MINUTES")
    check(abs((refresh["exp"] - refresh["iat"]) - cfg.refresh_lifetime_days * 86400) <= 5, "refresh lifetime differs from JWT_REFRESH_TOKEN_LIFETIME_DAYS")
    check(access.get("token_type") == "access" and refresh.get("token_type") == "refresh", "unexpected token_type claims")


def test_token_payload_carries_no_secret_fields(tokens):
    """TC-001-JWT-03: the (unencrypted) JWT payload holds no password/hash/email."""
    claims = jwt_claims(tokens("CUSTOMER")["access"])
    for key in claims:
        check(key.lower() not in {"password", "password_hash", "email", "phone"}, f"JWT payload exposes {key!r}")


def test_wrong_password_rejected_with_generic_message(auth_api, creds):
    """TC-001-JWT-04"""
    c = creds("CUSTOMER")
    assert_error(auth_api.obtain(c.username, WRONG_PASSWORD), 401, "INVALID_CREDENTIALS")


def test_unknown_user_and_wrong_password_are_indistinguishable(auth_api, creds):
    """TC-001-JWT-05: same status and identical body — never reveals which part was wrong."""
    c = creds("CUSTOMER")
    wrong_pw = auth_api.obtain(c.username, WRONG_PASSWORD)
    unknown = auth_api.obtain("qa_no_such_user_zz9", WRONG_PASSWORD)
    assert_error(unknown, 401, "INVALID_CREDENTIALS")
    check(wrong_pw.status_code == unknown.status_code, "status differs between unknown user and wrong password")
    check(wrong_pw.json() == unknown.json(), f"bodies differ: {describe(wrong_pw)} vs {describe(unknown)}")


def test_username_is_case_sensitive(auth_api, creds):
    """TC-001-JWT-06: login is case-sensitive (api-contracts § Identity rules)."""
    c = creds("CUSTOMER")
    swapped = c.username.swapcase()
    if swapped == c.username:
        pytest.skip("QA username has no letters to swap case")
    assert_error(auth_api.obtain(swapped, c.password), 401, "INVALID_CREDENTIALS")


def test_inactive_user_gets_the_same_401(auth_api, cfg, creds):
    """TC-001-JWT-07: inactive user -> same 401 INVALID_CREDENTIALS as a wrong password.

    Needs an inactive QA user (QA_INACTIVE_USERNAME/PASSWORD). `make seed-qa-users` does not
    create one yet (open item in test-strategy §12); skipped with that reason until it does.
    """
    inactive = cfg.optional_credentials("INACTIVE")
    if inactive is None:
        pytest.skip("no inactive QA user seeded (QA_INACTIVE_USERNAME/PASSWORD) — coverage gap, see test-strategy §12")
    c = creds("CUSTOMER")
    ref = auth_api.obtain(c.username, WRONG_PASSWORD)
    resp = auth_api.obtain(inactive.username, inactive.password)
    assert_error(resp, 401, "INVALID_CREDENTIALS")
    check(resp.json() == ref.json(), "inactive-user body differs from wrong-password body")


def test_refresh_returns_new_access_only(auth_api, tokens):
    """TC-001-JWT-08: no rotation in the MVP (JWT_ROTATE_REFRESH_TOKENS=False)."""
    resp = auth_api.refresh(tokens("CUSTOMER")["refresh"])
    data = assert_success(resp, 200)
    register_tokens(data)
    check(set(data) == {"access"}, f"refresh must return only 'access': {sorted(data)}")
    check(jwt_claims(data["access"]).get("token_type") == "access", "refreshed token is not an access token")


def test_refresh_with_tampered_token(auth_api, tokens):
    """TC-001-JWT-09"""
    assert_error(auth_api.refresh(jwt_tamper_signature(tokens("CUSTOMER")["refresh"])), 401, "TOKEN_INVALID")


def test_refresh_with_access_token_is_rejected(auth_api, tokens):
    """TC-001-JWT-10: token_type confusion."""
    assert_error(auth_api.refresh(tokens("CUSTOMER")["access"]), 401, "TOKEN_INVALID")


def test_refresh_with_garbage(auth_api):
    """TC-001-JWT-11"""
    assert_error(auth_api.refresh("not.a.jwt"), 401, "TOKEN_INVALID")


def test_refresh_missing_field(auth_api):
    """TC-001-JWT-12"""
    assert_error(auth_api.refresh(None), 400, fields=("refresh",))


def test_me_with_tampered_access_token(api, tokens):
    """TC-001-JWT-13: signature tampered -> 401 TOKEN_INVALID."""
    bad = jwt_tamper_signature(tokens("CUSTOMER")["access"])
    assert_error(api.get("/api/users/me/", headers={"Authorization": f"Bearer {bad}"}), 401, "TOKEN_INVALID")


def test_me_with_forged_claims_or_alg_none(api, tokens):
    """TC-001-JWT-14: payload changed (role/user_id/exp) with the old signature, or alg=none."""
    access = tokens("CUSTOMER")["access"]
    claims = jwt_claims(access)
    forged = [
        jwt_tamper_payload(access, exp=int(time.time()) + 10 * 86400),
        jwt_tamper_payload(access, user_id=(claims.get("user_id") or 0) + 1 if isinstance(claims.get("user_id"), int) else "1"),
        jwt_alg_none(access),
    ]
    for token in forged:
        assert_error(api.get("/api/users/me/", headers={"Authorization": f"Bearer {token}"}), 401, "TOKEN_INVALID")


def test_me_with_refresh_token_as_bearer(api, tokens):
    """TC-001-JWT-15: a refresh token is not an access token."""
    refresh = tokens("CUSTOMER")["refresh"]
    assert_error(api.get("/api/users/me/", headers={"Authorization": f"Bearer {refresh}"}), 401, "TOKEN_INVALID")


def test_me_with_expired_looking_token(api, tokens):
    """TC-001-JWT-16: exp in the past (signature therefore invalid). A genuinely expired,
    validly-signed token needs a 30-minute wait; that variant is run manually in TASK-009 and
    recorded in the report (plan TC-001-JWT-16b)."""
    expired = jwt_tamper_payload(tokens("CUSTOMER")["access"], exp=int(time.time()) - 60)
    assert_error(api.get("/api/users/me/", headers={"Authorization": f"Bearer {expired}"}), 401, "TOKEN_INVALID")
