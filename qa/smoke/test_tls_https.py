"""TLS, redirects and HSTS for both Flash domains (FEAT-004 AC5, AC6; ADR-015).

Plan: FEAT-004 TC-004-TLS-01..05.
"""

import datetime as dt
import socket
import ssl

import httpx
import pytest

from harness.envelope import check

pytestmark = [pytest.mark.smoke, pytest.mark.deploy, pytest.mark.regression, pytest.mark.security]


def _peer_cert(host: str) -> dict:
    ctx = ssl.create_default_context()  # verifies chain + hostname against the system CA store
    with socket.create_connection((host, 443), timeout=15) as sock:
        with ctx.wrap_socket(sock, server_hostname=host) as tls:
            return tls.getpeercert()


@pytest.fixture(scope="module", params=["api", "web"])
def host(request, cfg):
    return cfg.api_host if request.param == "api" else cfg.web_host


def test_certificate_valid_chain_and_hostname(host):
    """TC-004-TLS-01: a publicly trusted chain valid for the host (verification errors fail)."""
    cert = _peer_cert(host)
    check(bool(cert), f"no certificate returned by {host}")


def test_certificate_covers_exactly_the_two_flash_domains(host, cfg):
    """TC-004-TLS-02: one cert `flash-delivery` for exactly API_DOMAIN + WEB_DOMAIN, no dental name."""
    sans = {v for k, v in _peer_cert(host).get("subjectAltName", ()) if k == "DNS"}
    check(sans == {cfg.api_host, cfg.web_host}, f"{host}: SANs {sorted(sans)} != the two Flash domains")


def test_certificate_expiry(host, cfg):
    """TC-004-TLS-03: expires in more than QA_CERT_MIN_DAYS (default 60) days."""
    not_after = dt.datetime.fromtimestamp(ssl.cert_time_to_seconds(_peer_cert(host)["notAfter"]), dt.timezone.utc)
    days = (not_after - dt.datetime.now(dt.timezone.utc)).days
    check(days > cfg.cert_min_days, f"{host}: certificate expires in {days} days (min {cfg.cert_min_days})")


def test_http_redirects_to_https(host, cfg):
    """TC-004-TLS-04: http:// -> 301 to the same https:// URL (path and query kept)."""
    with httpx.Client(timeout=cfg.http_timeout, follow_redirects=False) as client:
        resp = client.get(f"http://{host}/qa/redirect-probe?x=1")
    check(resp.status_code == 301, f"{host}: HTTP returned {resp.status_code}, expected 301")
    check(resp.headers.get("location") == f"https://{host}/qa/redirect-probe?x=1", f"{host}: bad Location {resp.headers.get('location')!r}")


def test_hsts_without_include_subdomains(host, cfg):
    """TC-004-TLS-05: HSTS max-age=31536000, no includeSubDomains, no preload (parent shared with dental)."""
    with httpx.Client(timeout=cfg.http_timeout, follow_redirects=False) as client:
        resp = client.get(f"https://{host}/")
    hsts = resp.headers.get("strict-transport-security", "")
    check("max-age=31536000" in hsts, f"{host}: HSTS missing or wrong: {hsts!r}")
    check("includesubdomains" not in hsts.lower(), f"{host}: HSTS must not include subdomains: {hsts!r}")
    check("preload" not in hsts.lower(), f"{host}: HSTS must not preload: {hsts!r}")
