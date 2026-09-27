"""JWT login/refresh and /api/users/me/ (api-contracts.md § Identity)."""

from datetime import timedelta

import pytest
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

pytestmark = pytest.mark.django_db

TEST_PASSWORD = "Str0ng-test-passw0rd!"  # noqa: S105 - same default as the make_user fixture

TOKEN_URL = "/api/auth/token/"
REFRESH_URL = "/api/auth/token/refresh/"
ME_URL = "/api/users/me/"

INVALID_CREDENTIALS = {
    "success": False,
    "message": "Invalid username or password.",
    "errors": {"code": "INVALID_CREDENTIALS"},
}
TOKEN_INVALID = {
    "success": False,
    "message": "Token is invalid or expired.",
    "errors": {"code": "TOKEN_INVALID"},
}


def login(client, username, password=TEST_PASSWORD):
    return client.post(TOKEN_URL, {"username": username, "password": password}, format="json")


# --- Token obtain ------------------------------------------------------------------


def test_login_returns_access_and_refresh(api_client, make_user):
    user = make_user("driver1", role="DRIVER")

    response = login(api_client, "driver1")

    body = response.json()
    assert response.status_code == 200
    assert body["success"] is True
    assert set(body["data"]) == {"access", "refresh"}
    assert str(AccessToken(body["data"]["access"])["user_id"]) == str(user.pk)


def test_login_with_wrong_password_returns_invalid_credentials(api_client, make_user):
    make_user("driver1")

    response = login(api_client, "driver1", "wrong-password")

    assert response.status_code == 401
    assert response.json() == INVALID_CREDENTIALS


def test_login_with_unknown_user_returns_the_same_response(api_client):
    response = login(api_client, "nobody")

    assert response.status_code == 401
    assert response.json() == INVALID_CREDENTIALS


def test_login_with_inactive_user_returns_the_same_response(api_client, make_user):
    make_user("sleeper", is_active=False)

    response = login(api_client, "sleeper")

    assert response.status_code == 401
    assert response.json() == INVALID_CREDENTIALS


def test_login_is_case_sensitive(api_client, make_user):
    make_user("Driver1")

    assert login(api_client, "driver1").status_code == 401


@pytest.mark.parametrize("missing", ["username", "password"])
def test_login_missing_field_is_a_field_error(api_client, missing):
    payload = {"username": "a", "password": "b"}
    payload.pop(missing)

    response = api_client.post(TOKEN_URL, payload, format="json")

    body = response.json()
    assert response.status_code == 400
    assert body["message"] == "Validation failed."
    assert body["errors"][missing] == ["This field is required."]


def test_login_ignores_a_stale_bearer_header(api_client, make_user):
    make_user("driver1")
    api_client.credentials(HTTP_AUTHORIZATION="Bearer stale")

    assert login(api_client, "driver1").status_code == 200


def test_login_rejects_get(api_client):
    response = api_client.get(TOKEN_URL)

    assert response.status_code == 405


# --- Refresh -----------------------------------------------------------------------


def test_refresh_returns_new_access_without_rotation(api_client, user):
    refresh = RefreshToken.for_user(user)

    response = api_client.post(REFRESH_URL, {"refresh": str(refresh)}, format="json")

    body = response.json()
    assert response.status_code == 200
    assert set(body["data"]) == {"access"}
    assert str(AccessToken(body["data"]["access"])["user_id"]) == str(user.pk)


def test_refresh_with_invalid_token_returns_token_invalid(api_client):
    response = api_client.post(REFRESH_URL, {"refresh": "garbage"}, format="json")

    assert response.status_code == 401
    assert response.json() == TOKEN_INVALID


def test_refresh_with_expired_token_returns_token_invalid(api_client, user):
    refresh = RefreshToken.for_user(user)
    refresh.set_exp(lifetime=-timedelta(seconds=1))

    response = api_client.post(REFRESH_URL, {"refresh": str(refresh)}, format="json")

    assert response.status_code == 401
    assert response.json() == TOKEN_INVALID


def test_refresh_with_access_token_returns_token_invalid(api_client, user):
    access = AccessToken.for_user(user)

    response = api_client.post(REFRESH_URL, {"refresh": str(access)}, format="json")

    assert response.status_code == 401
    assert response.json()["errors"]["code"] == "TOKEN_INVALID"


def test_refresh_missing_field_is_a_field_error(api_client):
    response = api_client.post(REFRESH_URL, {}, format="json")

    assert response.status_code == 400
    assert response.json()["errors"]["refresh"] == ["This field is required."]


def test_token_lifetimes_come_from_settings(settings):
    jwt = settings.SIMPLE_JWT

    assert jwt["ACCESS_TOKEN_LIFETIME"] == timedelta(minutes=30)
    assert jwt["REFRESH_TOKEN_LIFETIME"] == timedelta(days=7)
    assert jwt["ROTATE_REFRESH_TOKENS"] is False


# --- /api/users/me/ ------------------------------------------------------------------


def test_me_returns_the_identity(api_client, make_user):
    user = make_user("store1", role="STORE")
    token = login(api_client, "store1").json()["data"]["access"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    response = api_client.get(ME_URL)

    assert response.status_code == 200
    assert response.json()["data"] == {
        "id": user.pk,
        "username": "store1",
        "role": "STORE",
        "is_staff": False,
    }


def test_me_without_credentials_is_not_authenticated(api_client):
    response = api_client.get(ME_URL)

    assert response.status_code == 401
    assert response.json() == {
        "success": False,
        "message": "Authentication credentials were not provided.",
        "errors": {"code": "NOT_AUTHENTICATED"},
    }


def test_me_with_bad_token_is_token_invalid(api_client):
    api_client.credentials(HTTP_AUTHORIZATION="Bearer not.a.token")

    response = api_client.get(ME_URL)

    assert response.status_code == 401
    assert response.json() == TOKEN_INVALID


def test_me_with_token_of_inactive_user_is_token_invalid(api_client, make_user):
    user = make_user("gone")
    token = AccessToken.for_user(user)
    user.is_active = False
    user.save()
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    response = api_client.get(ME_URL)

    assert response.status_code == 401
    assert response.json()["errors"]["code"] == "TOKEN_INVALID"


@pytest.mark.parametrize("method", ["put", "patch", "post", "delete"])
def test_me_is_read_only(auth_client, user, method):
    response = getattr(auth_client, method)(ME_URL, {"role": "ADMIN"}, format="json")

    assert response.status_code == 405
    user.refresh_from_db()
    assert user.role == "CUSTOMER"


# --- Throttling --------------------------------------------------------------------


@pytest.mark.ratelimit
def test_auth_endpoint_uses_stricter_throttle(api_client, make_user, throttle_rates):
    make_user("driver1")
    throttle_rates(auth="2/minute", anon="100/minute")

    statuses = [login(api_client, "driver1").status_code for _ in range(3)]

    assert statuses == [200, 200, 429]
    response = api_client.post(REFRESH_URL, {"refresh": "x"}, format="json")
    assert response.status_code == 429
    assert response.json()["errors"]["code"] == "THROTTLED"


@pytest.mark.ratelimit
def test_failed_logins_are_throttled(api_client, throttle_rates):
    throttle_rates(auth="2/minute")

    statuses = [login(api_client, "nobody", "guess").status_code for _ in range(3)]

    assert statuses == [401, 401, 429]


@pytest.mark.ratelimit
def test_me_uses_user_throttle(auth_client, throttle_rates):
    throttle_rates(user="1/minute", auth="100/minute")

    assert auth_client.get(ME_URL).status_code == 200
    assert auth_client.get(ME_URL).status_code == 429
