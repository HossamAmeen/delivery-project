"""Status page (FEAT-003 AC3, AC6; ADR-019). Plan: FEAT-003 TC-003-E2E-10..13."""

import pytest
from playwright.sync_api import expect

from harness.envelope import check
from harness.pwa import API_REACHABLE, API_UNREACHABLE, DESKTOP, MOBILE, RETRY_BUTTON, TID_EMPTY, TID_ERROR, TID_LOADING, TID_SESSION_USER, TID_STATUS_OK

pytestmark = [pytest.mark.regression]


@pytest.mark.smoke
@pytest.mark.parametrize("viewport", [MOBILE, DESKTOP], ids=["mobile-360", "desktop-1280"])
def test_status_page_shows_api_reachable_via_status_endpoint(new_page, cfg, viewport):
    """TC-003-E2E-10: 'API reachable' from GET <API>/api/status/; never /api/health/."""
    page = new_page(viewport=viewport)
    urls: list[str] = []
    page.on("request", lambda r: urls.append(r.url))
    page.goto(f"{cfg.web_url}/status")
    expect(page.get_by_text(API_REACHABLE)).to_be_visible()
    check(any(u.startswith(f"{cfg.base_url}/api/status/") for u in urls), "status page did not call <API>/api/status/")
    check(not any("/api/health" in u for u in urls), "status page called /api/health (ADR-019)")
    expect(page.get_by_text(cfg.base_url).first).to_be_visible()


@pytest.mark.security
def test_status_page_logged_in_shows_username_and_role(new_page, cfg, ui_login, creds, auth_pacer):
    """TC-003-E2E-11: logged in, the status page also shows username + role from /api/users/me/."""
    page = new_page()
    api_calls: list[str] = []  # evidence: method, path, status (no bodies, no headers)
    page.on("response", lambda r: api_calls.append(f"{r.request.method} {r.url.split('?')[0]} -> {r.status}") if "/api/" in r.url else None)
    ui_login(page, "STORE")
    page.wait_for_url(lambda u: "/login" not in u)
    auth_pacer.acquire()  # the reload may refresh the access token
    page.goto(f"{cfg.web_url}/status")
    page.wait_for_load_state("networkidle")
    session = page.get_by_test_id(TID_SESSION_USER)
    check(session.count() == 1, f"signed-in user not shown on /status; browser API calls: {api_calls}")
    expect(session).to_contain_text(creds("STORE").username)
    expect(session).to_contain_text("Store")


def test_status_page_loading_then_unreachable_then_retry(new_page, cfg):
    """TC-003-E2E-12 (AC3): loading state while pending; unavailable state on network error;
    retry recovers. Uses request interception (reported as such)."""
    page = new_page(block_sw=True)
    held = []
    page.route(f"{cfg.base_url}/api/status/", lambda route: held.append(route))
    page.goto(f"{cfg.web_url}/status")
    expect(page.get_by_test_id(TID_LOADING).first).to_be_visible()
    page.wait_for_timeout(200)
    check(bool(held), "the status request was not issued")
    held.pop(0).abort("connectionrefused")
    expect(page.get_by_test_id(TID_ERROR).first).to_be_visible()
    expect(page.get_by_text(API_UNREACHABLE).first).to_be_visible()
    page.unroute(f"{cfg.base_url}/api/status/")
    page.get_by_role("button", name=RETRY_BUTTON).click()
    expect(page.get_by_test_id(TID_STATUS_OK)).to_be_visible()


def test_status_page_anonymous_shows_empty_session_state(new_page, cfg):
    """TC-003-E2E-20 (AC3): not signed in -> the session card uses the empty-state component."""
    page = new_page()
    page.goto(f"{cfg.web_url}/status")
    expect(page.get_by_test_id(TID_EMPTY)).to_be_visible()


def test_status_page_server_error_shows_error_state(new_page, cfg):
    """TC-003-E2E-13 (AC3): a 5xx envelope shows the error state with a retry, not a blank page."""
    from harness.pwa import envelope_error

    page = new_page(block_sw=True)
    page.route(f"{cfg.base_url}/api/status/", lambda route: route.fulfill(**envelope_error(500, "SERVER_ERROR", "Something went wrong.")))
    page.goto(f"{cfg.web_url}/status")
    expect(page.get_by_test_id(TID_ERROR).first).to_be_visible()
    expect(page.get_by_role("button", name=RETRY_BUTTON)).to_be_visible()
    expect(page.get_by_test_id(TID_STATUS_OK)).to_have_count(0)
