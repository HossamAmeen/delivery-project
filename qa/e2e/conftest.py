"""Playwright E2E configuration (FEAT-003; ADR-008, ADR-018).

- Chromium only, headless (pytest-playwright `--browser chromium`, pytest.ini).
- One worker: the harness does not install pytest-xdist, so tests run serially — the
  equivalent of Playwright's `--workers=1`, which bounds memory on the shared server.
- Viewports: 360 px (mobile) and 1280 px (desktop). Tests pick one with the `new_page`
  factory; responsive tests parametrize both.
- No tracing and no video: a trace stores typed values (passwords). A screenshot is saved
  to `.results/playwright/` when a test fails.
- Every UI action that makes the browser call /api/auth/* on the real server first calls
  `auth_pacer.acquire()` so the E2E run stays under the `auth` throttle. Mocked routes do not.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from harness.config import ROLE_AREAS
from harness.pwa import DESKTOP, LOGIN_BUTTON, PASSWORD_LABEL, USERNAME_LABEL

RESULTS = Path(__file__).resolve().parent.parent / ".results" / "playwright"


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):  # noqa: ARG001
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    return {**browser_type_launch_args, "headless": True, "args": ["--disable-dev-shm-usage"]}


@pytest.fixture
def new_page(browser, cfg, request):
    """Factory: ``new_page(viewport=DESKTOP, block_sw=False)`` -> a Page in a fresh context.

    ``block_sw=True`` blocks the service worker so `page.route` interception is reliable.
    """
    contexts = []

    def make(viewport: dict | None = None, block_sw: bool = False):
        ctx = browser.new_context(
            viewport=viewport or DESKTOP,
            locale="en-US",
            service_workers="block" if block_sw else "allow",
        )
        ctx.set_default_timeout(15_000)
        contexts.append(ctx)
        return ctx.new_page()

    yield make

    failed = getattr(request.node, "rep_call", None) is not None and request.node.rep_call.failed
    for i, ctx in enumerate(contexts):
        if failed:
            RESULTS.mkdir(parents=True, exist_ok=True)
            safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", request.node.nodeid)[-150:]
            for j, pg in enumerate(ctx.pages):
                try:
                    pg.screenshot(path=str(RESULTS / f"{safe}-{i}-{j}.png"), full_page=True)
                except Exception:  # noqa: BLE001 - evidence is best effort
                    pass
        ctx.close()


@pytest.fixture
def ui_login(cfg, creds, auth_pacer):
    """Log in through the real /login form. Returns the role area path expected afterwards."""

    def login(page, role: str, password: str | None = None) -> str:
        c = creds(role)
        page.goto(f"{cfg.web_url}/login")
        page.get_by_label(USERNAME_LABEL).fill(c.username)
        page.get_by_label(PASSWORD_LABEL).fill(password if password is not None else c.password.reveal())
        auth_pacer.acquire()
        page.get_by_role("button", name=LOGIN_BUTTON).click()
        return ROLE_AREAS[role.upper()]

    return login

