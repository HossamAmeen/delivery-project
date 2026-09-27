"""OpenAPI schema and docs access (DRF_SKILL §21, §76; ADR-019)."""

import pytest
from django.core.management import call_command
from drf_spectacular.generators import SchemaGenerator
from rest_framework_simplejwt.tokens import RefreshToken

pytestmark = pytest.mark.django_db

DOC_URLS = ["/api/schema/", "/api/docs/", "/api/redoc/"]
HTTP_METHODS = {"get", "post", "put", "patch", "delete"}


@pytest.fixture
def schema():
    return SchemaGenerator().get_schema(request=None, public=True)


def operations(schema):
    for path, item in schema["paths"].items():
        for method, operation in item.items():
            if method in HTTP_METHODS:
                yield path, method, operation


def bearer(user) -> str:
    return f"Bearer {RefreshToken.for_user(user).access_token}"


def test_schema_generation_validates_without_warnings(tmp_path):
    output = tmp_path / "schema.yml"

    call_command("spectacular", "--validate", "--fail-on-warn", "--file", str(output))

    assert output.read_text().startswith("openapi: 3")


def test_schema_documents_expected_paths(schema):
    assert {
        "/api/status/",
        "/api/health/",
        "/api/health/ready/",
        "/api/auth/token/",
        "/api/auth/token/refresh/",
        "/api/users/me/",
    } <= set(schema["paths"])
    for docs_path in DOC_URLS:
        assert docs_path not in schema["paths"]


def test_every_operation_documents_429(schema):
    for path, method, operation in operations(schema):
        assert "429" in operation["responses"], (path, method)
    too_many = schema["components"]["responses"]["TooManyRequests"]
    assert "Retry-After" in too_many["headers"]


def test_success_responses_are_documented_with_the_envelope(schema):
    for path, method, operation in operations(schema):
        for code, response in operation["responses"].items():
            if not code.startswith("2") or code == "204":
                continue
            envelope = response["content"]["application/json"]["schema"]
            assert envelope["required"] == ["success", "message", "data"], (path, method, code)


def test_status_schema_is_the_enveloped_status_object(schema):
    response = schema["paths"]["/api/status/"]["get"]["responses"]["200"]
    data = response["content"]["application/json"]["schema"]["properties"]["data"]

    assert data["$ref"].endswith("/Status")


def test_bearer_auth_scheme_is_declared(schema):
    schemes = schema["components"]["securitySchemes"]

    assert any(s.get("scheme") == "bearer" for s in schemes.values())


def test_error_envelope_component_is_declared(schema):
    error = schema["components"]["schemas"]["ErrorEnvelope"]

    assert set(error["properties"]) >= {"success", "message", "errors"}


# --- Access (ADR-019) ------------------------------------------------------------


@pytest.mark.parametrize("url", DOC_URLS)
def test_docs_are_public_when_api_docs_public(client, settings, url):
    settings.API_DOCS_PUBLIC = True

    response = client.get(url)

    assert response.status_code == 200


def test_public_schema_is_raw_not_enveloped(client, settings):
    settings.API_DOCS_PUBLIC = True

    response = client.get("/api/schema/", HTTP_ACCEPT="application/vnd.oai.openapi+json")

    body = response.json()
    assert "openapi" in body
    assert "success" not in body


@pytest.mark.parametrize("url", DOC_URLS)
def test_docs_require_authentication_in_production_mode(client, settings, url):
    settings.API_DOCS_PUBLIC = False

    response = client.get(url)

    assert response.status_code == 401
    assert response["Content-Type"].startswith("application/json")
    assert response.json() == {
        "success": False,
        "message": "Authentication credentials were not provided.",
        "errors": {"code": "NOT_AUTHENTICATED"},
    }


@pytest.mark.parametrize("url", DOC_URLS)
def test_docs_refuse_non_staff_users(client, settings, make_user, url):
    settings.API_DOCS_PUBLIC = False
    user = make_user("customer")

    response = client.get(url, HTTP_AUTHORIZATION=bearer(user))

    assert response.status_code == 403
    assert response["Content-Type"].startswith("application/json")
    body = response.json()
    assert body["success"] is False
    assert body["errors"]["code"] == "PERMISSION_DENIED"


def test_schema_allowed_for_staff_bearer(client, settings, make_user):
    settings.API_DOCS_PUBLIC = False
    staff = make_user("staffer", is_staff=True)

    response = client.get(
        "/api/schema/",
        HTTP_AUTHORIZATION=bearer(staff),
        HTTP_ACCEPT="application/vnd.oai.openapi+json",
    )

    assert response.status_code == 200
    assert "openapi" in response.json()


@pytest.mark.parametrize("url", DOC_URLS)
def test_docs_allowed_for_staff_admin_session(client, settings, make_user, url):
    settings.API_DOCS_PUBLIC = False
    staff = make_user("staffer", is_staff=True)
    client.force_login(staff)

    response = client.get(url)

    assert response.status_code == 200
