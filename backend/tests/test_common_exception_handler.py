"""Exception handler: one test per error type (DRF_SKILL §20, api-contracts § Error codes)."""

import logging

import pytest

pytestmark = [pytest.mark.django_db, pytest.mark.urls("tests.testapp.urls")]


def assert_error(response, status, code, message=None):
    body = response.json()
    assert response.status_code == status
    assert body["success"] is False
    assert isinstance(body["message"], str) and body["message"]
    assert body["errors"]["code"] == code
    if message is not None:
        assert body["message"] == message
    return body


def test_field_validation_error_keeps_field_errors_without_code(api_client):
    response = api_client.post("/t/validate/", {"name": "too-long-name"}, format="json")

    body = response.json()
    assert response.status_code == 400
    assert body == {
        "success": False,
        "message": "Validation failed.",
        "errors": {"name": ["Ensure this field has no more than 5 characters."]},
    }


def test_missing_field_is_reported_under_the_field(api_client):
    response = api_client.post("/t/validate/", {}, format="json")

    assert response.status_code == 400
    assert response.json()["errors"]["name"] == ["This field is required."]


def test_non_field_validation_error_carries_validation_error_code(api_client):
    response = api_client.post("/t/validate/", {"name": "clash"}, format="json")

    body = assert_error(response, 400, "VALIDATION_ERROR", "Validation failed.")
    assert body["errors"]["non_field_errors"] == ["Name clashes with another widget."]


def test_django_validation_error_is_converted(api_client):
    response = api_client.get("/t/raise/django-validation/")

    body = assert_error(response, 400, "VALIDATION_ERROR")
    assert body["errors"]["non_field_errors"] == ["Bad value."]


def test_not_authenticated_returns_401(api_client):
    response = api_client.get("/t/private/")

    assert_error(
        response, 401, "NOT_AUTHENTICATED", "Authentication credentials were not provided."
    )


def test_authentication_failed_returns_token_invalid(api_client):
    response = api_client.get("/t/raise/auth-failed/")

    body = assert_error(response, 401, "TOKEN_INVALID", "Token is invalid or expired.")
    assert "internal token detail" not in str(body)


def test_invalid_bearer_token_returns_token_invalid(api_client):
    api_client.credentials(HTTP_AUTHORIZATION="Bearer not-a-real-token")

    response = api_client.get("/t/private/")

    assert_error(response, 401, "TOKEN_INVALID", "Token is invalid or expired.")


def test_permission_denied_returns_403(api_client):
    response = api_client.get("/t/raise/permission/")

    assert_error(response, 403, "PERMISSION_DENIED")


def test_django_permission_denied_is_converted(api_client):
    response = api_client.get("/t/raise/django-permission/")

    body = assert_error(response, 403, "PERMISSION_DENIED")
    assert "internal reason" not in str(body)


def test_http404_returns_not_found(api_client):
    response = api_client.get("/t/raise/not-found/")

    body = assert_error(response, 404, "NOT_FOUND", "Not found.")
    assert "secret-lookup-detail" not in str(body)


def test_method_not_allowed_returns_405(api_client):
    response = api_client.post("/t/public/", {}, format="json")

    assert_error(response, 405, "METHOD_NOT_ALLOWED")
    assert "GET" in response["Allow"]


def test_malformed_json_returns_parse_error(api_client):
    response = api_client.post("/t/validate/", data="{not json", content_type="application/json")

    assert_error(response, 400, "PARSE_ERROR")


def test_unsupported_media_type_returns_415(api_client):
    response = api_client.post("/t/validate/", data="<x/>", content_type="application/xml")

    assert_error(response, 415, "UNSUPPORTED_MEDIA_TYPE")


def test_throttled_returns_429_with_retry_after(api_client):
    response = api_client.get("/t/raise/throttled/")

    assert_error(response, 429, "THROTTLED", "Request rate limit exceeded.")
    assert response["Retry-After"] == "42"


def test_application_error_uses_its_code_and_status(api_client):
    response = api_client.get("/t/raise/conflict/")

    assert_error(response, 409, "INVALID_TRANSITION", "Cannot move.")


def test_business_validation_error_defaults(api_client):
    response = api_client.get("/t/raise/business-validation/")

    assert_error(response, 400, "VALIDATION_ERROR", "Validation failed.")


def test_application_error_extra_is_rendered_next_to_code(api_client):
    response = api_client.get("/t/raise/application/")

    body = assert_error(response, 400, "APPLICATION_ERROR")
    assert body["errors"]["field_hint"] == "x"


def test_other_client_errors_fall_back_to_their_default_code(api_client):
    response = api_client.get("/t/raise/teapot/")

    assert_error(response, 418, "TEAPOT", "I am a teapot.")


def test_generic_api_exception_is_a_server_error(api_client):
    response = api_client.get("/t/raise/custom-api/")

    assert_error(response, 500, "SERVER_ERROR", "An unexpected error occurred.")


def test_unexpected_exception_returns_generic_500_and_is_logged(api_client, caplog):
    with caplog.at_level(logging.ERROR, logger="common.exceptions"):
        response = api_client.get("/t/raise/unexpected/")

    body = assert_error(response, 500, "SERVER_ERROR", "An unexpected error occurred.")
    assert body["errors"] == {"code": "SERVER_ERROR"}
    text = response.content.decode()
    assert "secret internals" not in text
    assert "Traceback" not in text
    assert "/srv/flash" not in text
    assert any(record.exc_info for record in caplog.records)


def test_unknown_url_returns_enveloped_404(api_client):
    response = api_client.get("/t/does-not-exist/")

    assert_error(response, 404, "NOT_FOUND", "Not found.")


def test_django_server_error_handler_returns_envelope(rf):
    from common.views import server_error

    response = server_error(rf.get("/"))

    assert response.status_code == 500
    assert b'"SERVER_ERROR"' in response.content
