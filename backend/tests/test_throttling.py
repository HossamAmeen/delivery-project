"""Rate limiting (DRF_SKILL §61-77). Isolated LocMem cache, cleared per test."""

import pytest
from django.core.exceptions import ImproperlyConfigured

from common.throttling import (
    AnonRateThrottle,
    AuthRateThrottle,
    HealthRateThrottle,
    SensitiveRateThrottle,
    UserRateThrottle,
)

pytestmark = [pytest.mark.django_db, pytest.mark.urls("tests.testapp.urls"), pytest.mark.ratelimit]


def test_api_allows_requests_within_rate_limit(api_client, throttle_rates):
    throttle_rates(anon="3/minute")

    statuses = [api_client.get("/t/public/").status_code for _ in range(3)]

    assert statuses == [200, 200, 200]


def test_api_rejects_requests_after_rate_limit(api_client, throttle_rates):
    throttle_rates(anon="2/minute")
    for _ in range(2):
        api_client.get("/t/public/")

    response = api_client.get("/t/public/")

    assert response.status_code == 429
    body = response.json()
    assert body == {
        "success": False,
        "message": "Request rate limit exceeded.",
        "errors": {"code": "THROTTLED"},
    }
    assert int(response["Retry-After"]) > 0


def test_anonymous_user_uses_anonymous_throttle(api_client, throttle_rates):
    throttle_rates(anon="1/minute", user="100/minute")

    assert api_client.get("/t/public/").status_code == 200
    assert api_client.get("/t/public/").status_code == 429


def test_authenticated_user_uses_user_throttle(auth_client, throttle_rates):
    throttle_rates(anon="1/minute", user="3/minute")

    statuses = [auth_client.get("/t/private/").status_code for _ in range(4)]

    # The anon limit (1) does not apply to an authenticated user; the user limit (3) does.
    assert statuses == [200, 200, 200, 429]


def test_user_throttle_is_per_user_not_per_ip(api_client, make_user, throttle_rates):
    throttle_rates(user="1/minute")
    alice, bob = make_user("alice"), make_user("bob")

    api_client.force_authenticate(alice)
    assert api_client.get("/t/private/").status_code == 200
    assert api_client.get("/t/private/").status_code == 429
    api_client.force_authenticate(bob)
    assert api_client.get("/t/private/").status_code == 200


def test_sensitive_endpoint_has_stricter_rate_limit(api_client, throttle_rates):
    throttle_rates(anon="100/minute", sensitive="2/minute")

    statuses = [api_client.get("/t/sensitive/").status_code for _ in range(3)]

    assert statuses == [200, 200, 429]
    # The normal endpoint is still available with the looser anon limit.
    assert api_client.get("/t/public/").status_code == 200


def test_default_rates_are_stricter_for_auth_and_sensitive(settings):
    rates = settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]

    def per_minute(rate):
        count, period = rate.split("/")
        return int(count) / {"second": 1 / 60, "minute": 1, "hour": 60, "day": 1440}[period]

    assert set(rates) == {"anon", "user", "auth", "sensitive", "health"}
    assert per_minute(rates["auth"]) < per_minute(rates["anon"])
    assert per_minute(rates["sensitive"]) < per_minute(rates["user"])


def test_scopes_of_custom_throttles():
    assert AnonRateThrottle.scope == "anon"
    assert UserRateThrottle.scope == "user"
    assert AuthRateThrottle.scope == "auth"
    assert SensitiveRateThrottle.scope == "sensitive"
    assert HealthRateThrottle.scope == "health"


def test_missing_rate_raises_improperly_configured(settings):
    rest = dict(settings.REST_FRAMEWORK)
    rest["DEFAULT_THROTTLE_RATES"] = {"anon": "1/minute"}
    settings.REST_FRAMEWORK = rest

    with pytest.raises(ImproperlyConfigured):
        SensitiveRateThrottle()


def test_one_trusted_proxy_uses_forwarded_client_ip(api_client, settings, throttle_rates):
    throttle_rates(anon="1/minute")
    settings.REST_FRAMEWORK = {**settings.REST_FRAMEWORK, "NUM_PROXIES": 1}

    first = api_client.get("/t/public/", HTTP_X_FORWARDED_FOR="203.0.113.1")
    second_same_ip = api_client.get("/t/public/", HTTP_X_FORWARDED_FOR="203.0.113.1")
    other_ip = api_client.get("/t/public/", HTTP_X_FORWARDED_FOR="203.0.113.2")

    assert (first.status_code, second_same_ip.status_code, other_ip.status_code) == (
        200,
        429,
        200,
    )


def test_without_trusted_proxy_spoofed_header_does_not_bypass_limit(api_client, throttle_rates):
    throttle_rates(anon="1/minute")

    api_client.get("/t/public/", HTTP_X_FORWARDED_FOR="203.0.113.1")
    response = api_client.get("/t/public/", HTTP_X_FORWARDED_FOR="203.0.113.2")

    assert response.status_code == 429
