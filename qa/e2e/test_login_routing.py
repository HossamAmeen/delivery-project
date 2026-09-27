"""Login (username + password), role-area routing, logout, deep links (FEAT-003 AC4, AC6;
ADR-011; BLK-001). Uses the real server and the seeded QA users.
Plan: FEAT-003 TC-003-E2E-03..09.
"""

import re

import pytest
from playwright.sync_api import expect

from harness.config import ROLE_AREAS, ROLES
from harness.pwa import LOGOUT_BUTTON, MOBILE, NOT_FOUND, PASSWORD_LABEL

pytestmark = [pytest.mark.regression, pytest.mark.security]


def _area_url(cfg, area):
    return re.compile(rf"^{re.escape(cfg.web_url)}{re.escape(area)}(/.*)?$")


@pytest.mark.smoke
@pytest.mark.parametrize("role", ROLES)
def test_login_routes_each_role_to_its_area(new_page, cfg, ui_login, role):
    """TC-003-E2E-03"""
    page = new_page()
    area = ui_login(page, role)
    expect(page).to_have_url(_area_url(cfg, area))


def test_wrong_password_shows_the_api_message(new_page, cfg, ui_login):
    """TC-003-E2E-04: the INVALID_CREDENTIALS message is shown; the user stays on /login."""
    page = new_page()
    ui_login(page, "CUSTOMER", password="qa-wrong-password-!-0000")
    expect(page.get_by_text("Invalid username or password.")).to_be_visible()
    expect(page).to_have_url(re.compile(r"/login"))


def test_password_field_is_masked(new_page, cfg):
    """TC-003-E2E-05"""
    page = new_page()
    page.goto(f"{cfg.web_url}/login")
    expect(page.get_by_label(PASSWORD_LABEL)).to_have_attribute("type", "password")


def test_logout_returns_to_login_and_guards_the_area(new_page, cfg, ui_login):
    """TC-003-E2E-06: logout -> /login; the role area is no longer reachable."""
    page = new_page(viewport=MOBILE)
    area = ui_login(page, "DRIVER")
    expect(page).to_have_url(_area_url(cfg, area))
    page.get_by_role("button", name=LOGOUT_BUTTON).click()
    expect(page).to_have_url(re.compile(r"/login"))
    page.goto(f"{cfg.web_url}{area}")
    expect(page).to_have_url(re.compile(r"/login"))


def test_guard_sends_user_to_own_area(new_page, cfg, ui_login, auth_pacer):
    """TC-003-E2E-07: a customer opening /admin or /driver ends in /customer (ADR-011)."""
    page = new_page()
    area = ui_login(page, "CUSTOMER")
    expect(page).to_have_url(_area_url(cfg, area))
    for foreign in ("/admin", "/driver", "/store"):
        auth_pacer.acquire()  # a full page load may refresh the in-memory access token
        page.goto(f"{cfg.web_url}{foreign}")
        expect(page).to_have_url(_area_url(cfg, ROLE_AREAS["CUSTOMER"]))


def test_deep_link_logged_out_loads_app_and_redirects_to_login(new_page, cfg):
    """TC-003-E2E-08 (AC6): https://<web>/driver is served by the SPA (not nginx 404) -> /login."""
    page = new_page()
    resp = page.goto(f"{cfg.web_url}/driver")
    assert resp is not None and resp.status == 200
    expect(page).to_have_url(re.compile(r"/login"))


def test_unknown_route_shows_not_found_view(new_page, cfg):
    """TC-003-E2E-09: unknown client route -> the app's NotFound view (HTTP 200 from nginx)."""
    page = new_page()
    resp = page.goto(f"{cfg.web_url}/qa-no-such-route/deep")
    assert resp is not None and resp.status == 200
    expect(page.get_by_text(NOT_FOUND).first).to_be_visible()
