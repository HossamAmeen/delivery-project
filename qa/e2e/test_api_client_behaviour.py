"""API client behaviour (FEAT-003 AC2; api-contracts § Identity client rules).

Refresh/expiry/429 cannot be triggered live on demand (access tokens live 30 min and a live
429 would lock the suite out), so these tests use Playwright request interception with
contract-shaped envelopes. The QA report states this explicitly (TASK-010).
Plan: FEAT-003 TC-003-E2E-14..17.
"""

import re

import pytest
from playwright.sync_api import expect

from harness.envelope import check
from harness.pwa import (
    FAKE_ACCESS,
    FAKE_ACCESS_2,
    FAKE_REFRESH,
    LOGIN_BUTTON,
    PASSWORD_LABEL,
    RATE_LIMITED,
    USERNAME_LABEL,
    envelope_error,
    envelope_ok,
)

pytestmark = [pytest.mark.regression]

ME = {"id": 900001, "username": "qa_mock_customer", "role": "CUSTOMER", "is_staff": False}


def _mock_login(page, cfg, counts, me_handler, refresh_handler):
    def token(route):
        counts["token"] += 1
        route.fulfill(**envelope_ok({"access": FAKE_ACCESS, "refresh": FAKE_REFRESH}))

    def refresh(route):
        counts["refresh"] += 1
        refresh_handler(route)

    def me(route):
        counts["me"] += 1
        counts.setdefault("me_auth", []).append(route.request.headers.get("authorization", ""))
        me_handler(route)

    page.route(f"{cfg.base_url}/api/auth/token/", token)
    page.route(f"{cfg.base_url}/api/auth/token/refresh/", refresh)
    page.route(f"{cfg.base_url}/api/users/me/", me)


def _submit_login(page, cfg):
    page.goto(f"{cfg.web_url}/login")
    page.get_by_label(USERNAME_LABEL).fill("qa_mock_customer")
    page.get_by_label(PASSWORD_LABEL).fill("qa-mock-password")
    page.get_by_role("button", name=LOGIN_BUTTON).click()


def test_401_triggers_exactly_one_refresh_then_retry(new_page, cfg):
    """TC-003-E2E-14: /me 401 TOKEN_INVALID -> one refresh -> retried with the new access token."""
    page = new_page(block_sw=True)
    counts = {"token": 0, "refresh": 0, "me": 0}

    def me(route):
        if counts["me"] == 1:
            route.fulfill(**envelope_error(401, "TOKEN_INVALID", "Token is invalid or expired."))
        else:
            route.fulfill(**envelope_ok(ME))

    _mock_login(page, cfg, counts, me, lambda r: r.fulfill(**envelope_ok({"access": FAKE_ACCESS_2})))
    _submit_login(page, cfg)
    expect(page).to_have_url(re.compile(r"/customer"))
    check(counts["refresh"] == 1, f"expected exactly 1 refresh, got {counts['refresh']}")
    check(counts["me"] == 2, f"expected /me to be retried once (2 calls), got {counts['me']}")
    check(counts["me_auth"][-1] == f"Bearer {FAKE_ACCESS_2}", "retry did not use the refreshed access token")


def test_refresh_failure_logs_out(new_page, cfg):
    """TC-003-E2E-15: refresh 401 -> logout + redirect to /login; no refresh loop."""
    page = new_page(block_sw=True)
    counts = {"token": 0, "refresh": 0, "me": 0}
    _mock_login(
        page,
        cfg,
        counts,
        lambda r: r.fulfill(**envelope_error(401, "TOKEN_INVALID", "Token is invalid or expired.")),
        lambda r: r.fulfill(**envelope_error(401, "TOKEN_INVALID", "Token is invalid or expired.")),
    )
    _submit_login(page, cfg)
    page.wait_for_timeout(1500)
    expect(page).to_have_url(re.compile(r"/login"))
    check(counts["refresh"] == 1, f"expected exactly 1 refresh attempt, got {counts['refresh']}")
    stored = page.evaluate("() => JSON.stringify(Object.assign({}, window.localStorage))")
    check(FAKE_REFRESH not in stored, "the refresh token is still in localStorage after logout")


def test_login_429_shows_rate_limit_message(new_page, cfg):
    """TC-003-E2E-16: 429 THROTTLED on login -> a rate-limit message, not a generic error."""
    page = new_page(block_sw=True)
    page.route(
        f"{cfg.base_url}/api/auth/token/",
        lambda r: r.fulfill(**envelope_error(429, "THROTTLED", "Request rate limit exceeded.", headers={"Retry-After": "42"})),
    )
    _submit_login(page, cfg)
    expect(page.get_by_text(RATE_LIMITED).first).to_be_visible()


def test_status_429_shows_rate_limited_state(new_page, cfg):
    """TC-003-E2E-17: 429 on /api/status/ -> the status page shows 'rate-limited'."""
    page = new_page(block_sw=True)
    page.route(
        f"{cfg.base_url}/api/status/",
        lambda r: r.fulfill(**envelope_error(429, "THROTTLED", "Request rate limit exceeded.", headers={"Retry-After": "42"})),
    )
    page.goto(f"{cfg.web_url}/status")
    expect(page.get_by_text(RATE_LIMITED).first).to_be_visible()
