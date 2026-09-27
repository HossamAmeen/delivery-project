"""Cross-origin and transport-level API checks (FEAT-003 AC6; FEAT-004 backend settings, ADR-015).

Plan: FEAT-001 TC-001-SEC-01..03.
"""

import pytest

from harness.envelope import check, describe

pytestmark = [pytest.mark.regression, pytest.mark.security]


def _preflight(api, origin):
    return api.options(
        "/api/auth/token/",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,authorization",
        },
    )


def test_cors_allows_the_pwa_origin(api, cfg):
    """TC-001-SEC-01: CORS_ALLOWED_ORIGINS=https://${WEB_DOMAIN}."""
    resp = _preflight(api, cfg.web_url)
    check(resp.status_code in (200, 204), f"preflight rejected: {describe(resp)}")
    check(resp.headers.get("access-control-allow-origin") == cfg.web_url, f"ACAO must equal the web origin: {dict(resp.headers)}")


def test_cors_refuses_foreign_origins(api):
    """TC-001-SEC-02: other origins (incl. the dental app and a lookalike) get no ACAO."""
    for origin in ("https://evil.example", "https://dental.hossam-ameen.online", "https://delivery.hossam-ameen.online.evil.example"):
        resp = _preflight(api, origin)
        acao = resp.headers.get("access-control-allow-origin")
        check(acao not in (origin, "*"), f"origin {origin} allowed by CORS")


def test_api_security_headers(api):
    """TC-001-SEC-03: nosniff and HSTS on API responses (Django SecurityMiddleware / nginx)."""
    resp = api.get("/api/status/")
    # Fetch spec: the first value of the (combined) header list decides. A duplicated header
    # ("nosniff, nosniff") is still effective; the duplication is tracked as a hygiene bug.
    xcto = resp.headers.get("x-content-type-options", "")
    check(xcto.split(",")[0].strip().lower() == "nosniff", f"missing X-Content-Type-Options: nosniff: {dict(resp.headers)}")
    check("max-age=" in resp.headers.get("strict-transport-security", ""), "missing HSTS on the API")

