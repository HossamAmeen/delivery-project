"""Responsive layout at 360 px and 1280 px (FEAT-003 AC1; TASK-007). Plan: FEAT-003 TC-003-E2E-18."""

import pytest
from playwright.sync_api import expect

from harness.envelope import check
from harness.pwa import DESKTOP, MOBILE, PASSWORD_LABEL, USERNAME_LABEL, no_horizontal_overflow

pytestmark = [pytest.mark.regression]


@pytest.mark.parametrize("viewport", [MOBILE, DESKTOP], ids=["mobile-360", "desktop-1280"])
@pytest.mark.parametrize("path", ["/login", "/status", "/qa-no-such-route"])
def test_no_horizontal_overflow_and_labelled_inputs(new_page, cfg, viewport, path):
    """TC-003-E2E-18: no horizontal scroll; login inputs have accessible labels."""
    page = new_page(viewport=viewport)
    page.goto(f"{cfg.web_url}{path}")
    page.wait_for_load_state("networkidle")
    check(no_horizontal_overflow(page), f"horizontal overflow on {path} at {viewport['width']} px")
    if path == "/login":
        expect(page.get_by_label(USERNAME_LABEL)).to_be_visible()
        expect(page.get_by_label(PASSWORD_LABEL)).to_be_visible()
