"""OpenAPI schema and docs (FEAT-001 AC7; ADR-019: staff only in production).

Plan: FEAT-001 TC-001-DOC-01..07.
"""

import pytest

from harness.envelope import assert_error, check, describe

pytestmark = [pytest.mark.regression]

CONTRACT_PATHS = (
    "/api/status/",
    "/api/health/",
    "/api/health/ready/",
    "/api/auth/token/",
    "/api/auth/token/refresh/",
    "/api/users/me/",
)
HTTP_METHODS = {"get", "post", "put", "patch", "delete"}
# The docs UIs render HTML only; a browser Accept header is what real clients send. With
# Accept: application/json DRF answers 406 NOT_ACCEPTABLE (enveloped) before auth runs.
BROWSER_ACCEPT = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"


@pytest.fixture(scope="module")
def schema(api, auth_headers):
    resp = api.get("/api/schema/", params={"format": "json"}, headers={**auth_headers("ADMIN"), "Accept": "application/vnd.oai.openapi+json, application/json"})
    check(resp.status_code == 200, f"staff must read the schema: {describe(resp)}")
    try:
        doc = resp.json()
    except ValueError:
        pytest.fail(f"schema is not JSON with ?format=json: {describe(resp)}")
    return doc


def test_schema_readable_by_staff_and_raw(schema):
    """TC-001-DOC-01: OpenAPI 3 document, raw (not wrapped in the envelope)."""
    check(str(schema.get("openapi", "")).startswith("3."), "not an OpenAPI 3 document")
    check("success" not in schema, "schema must not be enveloped")


@pytest.mark.security
def test_schema_denied_to_anonymous(api):
    """TC-001-DOC-02"""
    assert_error(api.get("/api/schema/"), 401, "NOT_AUTHENTICATED")


@pytest.mark.security
@pytest.mark.parametrize("role", ["CUSTOMER", "DRIVER", "STORE"])
def test_schema_and_docs_denied_to_non_staff(api, auth_headers, role):
    """TC-001-DOC-03"""
    for path, accept in (("/api/schema/", "application/json"), ("/api/docs/", BROWSER_ACCEPT), ("/api/redoc/", BROWSER_ACCEPT)):
        assert_error(api.get(path, headers={**auth_headers(role), "Accept": accept}), 403, "PERMISSION_DENIED")


@pytest.mark.security
@pytest.mark.parametrize("path", ["/api/docs/", "/api/redoc/"])
def test_docs_ui_denied_to_anonymous(api, path):
    """TC-001-DOC-04"""
    resp = api.get(path, headers={"Accept": BROWSER_ACCEPT})
    assert_error(resp, 401, "NOT_AUTHENTICATED")


@pytest.mark.parametrize("path", ["/api/docs/", "/api/redoc/"])
def test_docs_ui_available_to_staff(api, auth_headers, path):
    """TC-001-DOC-05"""
    resp = api.get(path, headers={**auth_headers("ADMIN"), "Accept": "text/html"})
    check(resp.status_code == 200 and "text/html" in resp.headers.get("content-type", ""), f"docs UI not served to staff: {describe(resp, 200)}")


def test_schema_documents_contract_paths(schema):
    """TC-001-DOC-06: every Foundation/Identity contract path is in the live OpenAPI."""
    paths = schema.get("paths", {})
    missing = [p for p in CONTRACT_PATHS if p not in paths]
    check(not missing, f"contract paths missing from OpenAPI: {missing}")


def test_schema_documents_429_everywhere(schema):
    """TC-001-DOC-07: every API operation documents a 429 response (api-contracts §1.6)."""
    missing = []
    for path, item in schema.get("paths", {}).items():
        for method, op in item.items():
            if method in HTTP_METHODS and "429" not in {str(k) for k in (op.get("responses") or {})}:
                missing.append(f"{method.upper()} {path}")
    check(not missing, f"operations without a documented 429: {missing}")


def test_schema_declares_bearer_auth(schema):
    """TC-001-DOC-08: JWT bearer scheme declared (TASK-004)."""
    schemes = (schema.get("components") or {}).get("securitySchemes") or {}
    check(
        any(s.get("type") == "http" and str(s.get("scheme", "")).lower() == "bearer" for s in schemes.values()),
        f"no bearer security scheme: {sorted(schemes)}",
    )
