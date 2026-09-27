"""PWA installability in a real browser (FEAT-003 AC1). Plan: FEAT-003 TC-003-E2E-01..02."""

import pytest
from playwright.sync_api import expect

from harness.envelope import check
from harness.pwa import DESKTOP, MOBILE

pytestmark = [pytest.mark.regression]


@pytest.mark.smoke
@pytest.mark.parametrize("viewport", [MOBILE, DESKTOP], ids=["mobile-360", "desktop-1280"])
def test_app_loads_and_service_worker_registers(new_page, cfg, viewport):
    """TC-003-E2E-01: the app renders, links the manifest and a service worker becomes active."""
    page = new_page(viewport=viewport)
    page.goto(f"{cfg.web_url}/")
    expect(page.locator("#app")).not_to_be_empty()
    check(page.locator('link[rel="manifest"]').count() == 1, "index.html must link exactly one manifest")
    active = page.evaluate(
        """async () => {
            if (!('serviceWorker' in navigator)) return 'unsupported';
            const reg = await Promise.race([
                navigator.serviceWorker.ready,
                new Promise(r => setTimeout(() => r(null), 15000)),
            ]);
            return reg && reg.active ? 'active' : 'none';
        }"""
    )
    check(active == "active", f"service worker not active after 15 s ({active})")


def test_manifest_icons_resolve_in_browser(new_page, cfg):
    """TC-003-E2E-02: every manifest icon loads with an image type (browser fetch)."""
    page = new_page()
    page.goto(f"{cfg.web_url}/")
    bad = page.evaluate(
        """async () => {
            const href = document.querySelector('link[rel="manifest"]').href;
            const m = await (await fetch(href)).json();
            const bad = [];
            for (const i of m.icons || []) {
                const r = await fetch(new URL(i.src, href));
                if (!r.ok || !(r.headers.get('content-type') || '').startsWith('image/')) bad.push(i.src);
            }
            return bad;
        }"""
    )
    check(bad == [], f"icons failing to load: {bad}")
