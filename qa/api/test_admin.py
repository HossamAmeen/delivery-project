"""Django Admin (Jazzmin) is staff-only (FEAT-001 AC8; ADR-011) and the admin session opens
the OpenAPI docs (ADR-019). Form login with CSRF; no DRF throttle applies.

Plan: FEAT-001 TC-001-ADM-01..04.
"""

import re

import pytest

from harness.envelope import check, describe

pytestmark = [pytest.mark.regression, pytest.mark.security]

CSRF_RE = re.compile(r'name="csrfmiddlewaretoken"\s+value="([^"]+)"')


def admin_login(client, cfg, username, password):
    page = client.get("/admin/login/", headers={"Accept": "text/html"})
    check(page.status_code == 200, f"admin login page not served: {describe(page, 200)}")
    match = CSRF_RE.search(page.text)
    check(match is not None, "admin login form has no CSRF token")
    return client.post(
        "/admin/login/?next=/admin/",
        data={"csrfmiddlewaretoken": match.group(1), "username": username, "password": password.reveal(), "next": "/admin/"},
        headers={"Referer": f"{cfg.base_url}/admin/login/", "Accept": "text/html"},
    )


@pytest.mark.smoke
def test_admin_redirects_anonymous_to_login(fresh_api):
    """TC-001-ADM-01"""
    resp = fresh_api.get("/admin/", headers={"Accept": "text/html"})
    check(resp.status_code == 302 and "/admin/login/" in resp.headers.get("location", ""), f"anonymous not redirected to admin login: {describe(resp, 200)}")


@pytest.mark.parametrize("role", ["CUSTOMER", "DRIVER", "STORE"])
def test_admin_rejects_non_staff(fresh_api, cfg, creds, role):
    """TC-001-ADM-02: a non-staff user cannot log in to the admin and stays redirected."""
    c = creds(role)
    resp = admin_login(fresh_api, cfg, c.username, c.password)
    check(resp.status_code == 200, f"non-staff login must re-render the form (no redirect into /admin/): {describe(resp, 200)}")
    follow = fresh_api.get("/admin/", headers={"Accept": "text/html"})
    check(follow.status_code == 302 and "/admin/login/" in follow.headers.get("location", ""), f"{role} reached /admin/: {describe(follow, 200)}")


def test_admin_accepts_staff(fresh_api, cfg, creds):
    """TC-001-ADM-03: qa_admin (staff) logs in and sees the Jazzmin index."""
    c = creds("ADMIN")
    resp = admin_login(fresh_api, cfg, c.username, c.password)
    check(resp.status_code == 302 and resp.headers.get("location", "").endswith("/admin/"), f"staff login did not redirect to /admin/: {describe(resp, 200)}")
    index = fresh_api.get("/admin/", headers={"Accept": "text/html"})
    check(index.status_code == 200 and "text/html" in index.headers.get("content-type", ""), f"admin index not served: {describe(index, 200)}")
    cookie_hdrs = resp.headers.get_list("set-cookie")
    for hdr in cookie_hdrs:
        if hdr.lower().startswith(("sessionid", "csrftoken")):
            check("secure" in hdr.lower(), f"cookie without Secure flag: {hdr.split('=')[0]}")


def test_admin_session_opens_openapi(fresh_api, cfg, creds):
    """TC-001-ADM-04: staff admin session (no bearer) may read the schema (ADR-019)."""
    c = creds("ADMIN")
    admin_login(fresh_api, cfg, c.username, c.password)
    resp = fresh_api.get("/api/schema/", params={"format": "json"})
    check(resp.status_code == 200, f"staff session cannot read the schema: {describe(resp)}")
