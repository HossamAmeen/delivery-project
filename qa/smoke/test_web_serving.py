"""PWA served by nginx at WEB_DOMAIN (FEAT-003 AC1, AC6; FEAT-004 AC5; ADR-015, ADR-019).

HTTP-level checks (no browser). Browser checks live in qa/e2e/.
Plan: FEAT-003 TC-003-WEB-01..08, FEAT-004 TC-004-WEB-01..03.
"""

import re
from urllib.parse import urljoin

import pytest

from harness.envelope import check, describe

pytestmark = [pytest.mark.smoke, pytest.mark.deploy, pytest.mark.regression]

ASSET_RE = re.compile(r"""(?:src|href)=["'](/assets/[^"']+)["']""")
CHUNK_RE = re.compile(r"""["'(/]((?:\./|/)?assets/[A-Za-z0-9_.\-]+\.js)["')]""")


@pytest.fixture(scope="module")
def index(web):
    resp = web.get("/")
    check(resp.status_code == 200, f"web root: {describe(resp, 200)}")
    return resp


def _js_bundle(web, index_html: str, limit: int = 60) -> dict[str, str]:
    """index.html's scripts plus lazily imported chunks (breadth-first, bounded)."""
    queue = [p for p in ASSET_RE.findall(index_html) if p.endswith(".js")]
    seen: dict[str, str] = {}
    while queue and len(seen) < limit:
        path = queue.pop(0)
        if path in seen:
            continue
        resp = web.get(path)
        check(resp.status_code == 200, f"asset {path}: {resp.status_code}")
        seen[path] = resp.text
        for ref in CHUNK_RE.findall(resp.text):
            ref_path = "/" + ref.lstrip("./") if not ref.startswith("/") else ref
            if ref_path not in seen:
                queue.append(ref_path)
    return seen


def test_web_root_serves_the_app_shell(index):
    """TC-003-WEB-01"""
    check("text/html" in index.headers.get("content-type", ""), "root is not HTML")
    check('id="app"' in index.text, "app root element missing from index.html")


def test_index_is_not_cached(index):
    """TC-004-WEB-01: Cache-Control no-cache for index.html (ADR-015)."""
    check("no-cache" in index.headers.get("cache-control", ""), f"index.html Cache-Control: {index.headers.get('cache-control')!r}")


@pytest.mark.parametrize("path", ["/driver", "/customer", "/store", "/admin", "/login", "/status", "/qa/unknown/deep/link"])
def test_deep_links_load_the_app(web, path):
    """TC-003-WEB-02: SPA fallback — deep links and unknown routes return index.html, not a 404."""
    resp = web.get(path)
    check(resp.status_code == 200 and 'id="app"' in resp.text, f"deep link {path}: {describe(resp, 200)}")


def test_manifest_served_and_valid(web):
    """TC-003-WEB-03 (AC1): manifest fields per TASK-007; no-cache (ADR-015)."""
    resp = web.get("/manifest.webmanifest")
    check(resp.status_code == 200, f"manifest: {describe(resp, 200)}")
    check("no-cache" in resp.headers.get("cache-control", ""), f"manifest Cache-Control: {resp.headers.get('cache-control')!r}")
    m = resp.json()
    check(m.get("name") == "Flash" and m.get("short_name") == "Flash", f"name/short_name: {m.get('name')!r}/{m.get('short_name')!r}")
    check(m.get("start_url") == "/" and m.get("display") == "standalone", "start_url must be / and display standalone")
    sizes = {i.get("sizes") for i in m.get("icons", [])}
    check({"192x192", "512x512"} <= sizes, f"icons 192 and 512 required, got {sorted(s for s in sizes if s)}")
    check(any("maskable" in (i.get("purpose") or "") for i in m.get("icons", [])), "a maskable icon is required")
    for icon in m.get("icons", []):
        r = web.get(urljoin("/", icon["src"]))
        check(r.status_code == 200 and r.headers.get("content-type", "").startswith("image/"), f"icon {icon['src']}: {r.status_code} {r.headers.get('content-type')}")


def test_service_worker_served_no_cache(web):
    """TC-003-WEB-04: sw.js served as JavaScript with no-cache (ADR-015)."""
    resp = web.get("/sw.js")
    check(resp.status_code == 200, f"sw.js: {describe(resp, 200)}")
    check("javascript" in resp.headers.get("content-type", ""), f"sw.js content-type {resp.headers.get('content-type')!r}")
    check("no-cache" in resp.headers.get("cache-control", ""), f"sw.js Cache-Control: {resp.headers.get('cache-control')!r}")


def test_hashed_assets_are_immutable(web, index):
    """TC-004-WEB-02: /assets/ 1-year immutable."""
    assets = ASSET_RE.findall(index.text)
    check(bool(assets), "index.html references no /assets/ files")
    resp = web.get(assets[0])
    cc = resp.headers.get("cache-control", "")
    check(resp.status_code == 200 and "max-age=31536000" in cc and "immutable" in cc, f"{assets[0]} Cache-Control {cc!r}")


@pytest.mark.security
def test_bundle_has_no_health_token_and_targets_the_api_domain(web, index, cfg, health_token):
    """TC-003-WEB-05 (AC6, ADR-019): the built JS contains no health token, never calls
    /api/health/, and uses the configured API base URL."""
    bundle = _js_bundle(web, index.text)
    token = health_token.reveal()
    check(not any(token in js for js in bundle.values()), "health token found in the PWA bundle")
    check(not any("/api/health" in js for js in bundle.values()), "PWA bundle references /api/health (must use /api/status/)")
    check(any(cfg.base_url in js for js in bundle.values()), f"PWA bundle does not contain the API base URL {cfg.base_url}")
    check(not any("localhost:8000" in js or "127.0.0.1:8" in js for js in bundle.values()), "a local API URL is baked into the bundle")


@pytest.mark.security
def test_web_does_not_expose_source_maps_or_env(web):
    """TC-003-WEB-06: no .env / source tree served from the web root (returns the SPA or 404)."""
    for path in ("/.env", "/.git/config", "/package.json"):
        resp = web.get(path)
        check(not (resp.status_code == 200 and 'id="app"' not in resp.text), f"{path} is served as a file")


def test_api_static_admin_css_served_by_nginx(api):
    """TC-004-WEB-03: /static/ (collectstatic) served on the API domain."""
    resp = api.get("/static/admin/css/base.css", headers={"Accept": "text/css"})
    check(resp.status_code == 200 and "text/css" in resp.headers.get("content-type", ""), f"admin CSS: {describe(resp, 200)}")
