"""Health, readiness and status endpoints (DRF_SKILL §27, ADR-019)."""

import logging

import pytest

from apps.health import services

from .conftest import HEALTH_TOKEN

pytestmark = pytest.mark.django_db

HEALTH_URL = "/api/health/"
READY_URL = "/api/health/ready/"
STATUS_URL = "/api/status/"
INVALID = {
    "success": False,
    "message": "Invalid health check password.",
    "errors": {"code": "HEALTH_TOKEN_INVALID"},
}


# --- /api/health/ ----------------------------------------------------------------


def test_health_endpoint_returns_success_with_valid_password(api_client):
    response = api_client.get(HEALTH_URL, {"password": HEALTH_TOKEN})

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "message": "Operation completed successfully.",
        "data": {"status": "healthy"},
    }


def test_health_endpoint_accepts_header_token(api_client):
    response = api_client.get(HEALTH_URL, HTTP_X_HEALTH_CHECK_TOKEN=HEALTH_TOKEN)

    assert response.status_code == 200
    assert response.json()["data"] == {"status": "healthy"}
    assert response["Cache-Control"] == "no-store"


def test_health_endpoint_rejects_invalid_password(api_client):
    response = api_client.get(HEALTH_URL, {"password": "wrong"})

    assert response.status_code == 401
    assert response.json() == INVALID


def test_health_endpoint_rejects_invalid_header(api_client):
    response = api_client.get(HEALTH_URL, HTTP_X_HEALTH_CHECK_TOKEN="wrong")

    assert response.status_code == 401
    assert response.json() == INVALID


def test_health_endpoint_requires_password(api_client):
    response = api_client.get(HEALTH_URL)

    assert response.status_code == 401
    assert response.json() == INVALID


def test_health_endpoint_rejects_everything_when_no_password_configured(api_client, settings):
    settings.HEALTH_CHECK_PASSWORD = ""

    response = api_client.get(HEALTH_URL, {"password": ""})

    assert response.status_code == 401


def test_health_endpoint_does_not_expose_secret(api_client, caplog):
    with caplog.at_level(logging.DEBUG):
        ok = api_client.get(HEALTH_URL, HTTP_X_HEALTH_CHECK_TOKEN=HEALTH_TOKEN)
        bad = api_client.get(HEALTH_URL, {"password": "wrong"})
        ready = api_client.get(READY_URL, {"password": HEALTH_TOKEN})

    for response in (ok, bad, ready):
        assert HEALTH_TOKEN not in response.content.decode()
        assert HEALTH_TOKEN not in str(dict(response.headers))
    assert HEALTH_TOKEN not in caplog.text


def test_health_endpoint_ignores_a_bad_bearer_token(api_client):
    api_client.credentials(HTTP_AUTHORIZATION="Bearer stale")

    response = api_client.get(HEALTH_URL, HTTP_X_HEALTH_CHECK_TOKEN=HEALTH_TOKEN)

    assert response.status_code == 200


def test_health_token_comparison_uses_compare_digest(monkeypatch):
    calls = []
    real = services.hmac.compare_digest

    def spy(a, b):
        calls.append((a, b))
        return real(a, b)

    monkeypatch.setattr(services.hmac, "compare_digest", spy)

    assert services.health_token_matches(HEALTH_TOKEN) is True
    assert services.health_token_matches("nope") is False
    assert len(calls) == 2


@pytest.mark.ratelimit
def test_health_endpoint_uses_health_throttle_scope(api_client, throttle_rates):
    throttle_rates(health="2/minute", anon="100/minute")

    statuses = [
        api_client.get(HEALTH_URL, HTTP_X_HEALTH_CHECK_TOKEN=HEALTH_TOKEN).status_code
        for _ in range(3)
    ]

    assert statuses == [200, 200, 429]
    assert api_client.get(HEALTH_URL).json()["errors"]["code"] == "THROTTLED"


@pytest.mark.ratelimit
def test_health_is_not_limited_by_the_anon_scope(api_client, throttle_rates):
    throttle_rates(health="100/minute", anon="1/minute")

    statuses = [
        api_client.get(HEALTH_URL, HTTP_X_HEALTH_CHECK_TOKEN=HEALTH_TOKEN).status_code
        for _ in range(3)
    ]

    assert statuses == [200, 200, 200]


# --- /api/health/ready/ ------------------------------------------------------------


def test_readiness_returns_ready_with_celery_skipped(api_client, settings):
    settings.CELERY_ENABLED = False

    response = api_client.get(READY_URL, HTTP_X_HEALTH_CHECK_TOKEN=HEALTH_TOKEN)

    assert response.status_code == 200
    assert response.json()["data"] == {
        "status": "ready",
        "checks": {"database": "ok", "cache": "ok", "celery": "skipped"},
    }


def test_readiness_requires_token(api_client):
    response = api_client.get(READY_URL)

    assert response.status_code == 401
    assert response.json() == INVALID


def test_readiness_reports_database_failure_as_503(api_client, monkeypatch, caplog):
    class BrokenConnection:
        def cursor(self):
            raise RuntimeError("disk I/O error at /srv/flash/shared/db/flash.sqlite3")

    monkeypatch.setattr(services, "connections", {"default": BrokenConnection()})

    with caplog.at_level(logging.WARNING, logger="apps.health"):
        response = api_client.get(READY_URL, HTTP_X_HEALTH_CHECK_TOKEN=HEALTH_TOKEN)

    assert response.status_code == 503
    assert response.json() == {
        "success": False,
        "message": "Service not ready.",
        "errors": {
            "code": "SERVICE_NOT_READY",
            "checks": {"database": "error", "cache": "ok", "celery": "skipped"},
        },
    }
    assert "/srv/flash" not in response.content.decode()
    assert "Readiness check failed: database (RuntimeError)" in caplog.text


def test_readiness_reports_cache_failure_as_503(api_client, monkeypatch):
    class BrokenCache:
        def set(self, *args, **kwargs):
            raise OSError("cache dir not writable")

    monkeypatch.setattr(services, "cache", BrokenCache())

    response = api_client.get(READY_URL, HTTP_X_HEALTH_CHECK_TOKEN=HEALTH_TOKEN)

    assert response.status_code == 503
    assert response.json()["errors"]["checks"]["cache"] == "error"


def test_readiness_cache_value_not_read_back_is_an_error(monkeypatch):
    class ForgetfulCache:
        def set(self, *args, **kwargs):
            pass

        def get(self, key):
            return None

        def delete(self, key):
            pass

    monkeypatch.setattr(services, "cache", ForgetfulCache())

    assert services.check_cache() == services.ERROR


def test_readiness_cache_check_works_with_file_based_cache(settings, tmp_path):
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
            "LOCATION": str(tmp_path / "cache"),
        }
    }

    assert services.check_cache() == services.OK


def test_celery_not_checked_when_disabled(settings, monkeypatch):
    settings.CELERY_ENABLED = False
    import config

    monkeypatch.setattr(config, "celery_app", None)

    assert services.check_celery() == services.SKIPPED


def test_celery_checked_when_enabled(settings):
    pytest.importorskip("celery")
    settings.CELERY_ENABLED = True

    # The test app's broker is the in-memory transport.
    assert services.check_celery() == services.OK


def test_celery_broker_failure_when_enabled(settings, monkeypatch):
    pytest.importorskip("celery")
    settings.CELERY_ENABLED = True
    import config

    def boom():
        raise ConnectionError("redis://secret-host:6379 unreachable")

    monkeypatch.setattr(config.celery_app, "connection_for_write", boom)

    assert services.check_celery() == services.ERROR


def test_celery_enabled_but_not_installed_is_an_error(settings, monkeypatch):
    settings.CELERY_ENABLED = True
    import config

    monkeypatch.setattr(config, "celery_app", None)

    assert services.check_celery() == services.ERROR


def test_readiness_with_celery_enabled_and_broker_down_is_503(api_client, settings, monkeypatch):
    settings.CELERY_ENABLED = True
    monkeypatch.setitem(services.CHECKS, "celery", lambda: services.ERROR)

    response = api_client.get(READY_URL, HTTP_X_HEALTH_CHECK_TOKEN=HEALTH_TOKEN)

    assert response.status_code == 503
    assert response.json()["errors"]["checks"]["celery"] == "error"


# --- /api/status/ ------------------------------------------------------------------


def test_status_is_public_and_minimal(api_client):
    response = api_client.get(STATUS_URL)

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "message": "Operation completed successfully.",
        "data": {"status": "ok"},
    }


def test_status_ignores_a_bad_bearer_token(api_client):
    api_client.credentials(HTTP_AUTHORIZATION="Bearer stale")

    assert api_client.get(STATUS_URL).status_code == 200


@pytest.mark.ratelimit
def test_status_uses_health_throttle_scope(api_client, throttle_rates):
    throttle_rates(health="1/minute", anon="100/minute")

    assert api_client.get(STATUS_URL).status_code == 200
    response = api_client.get(STATUS_URL)
    assert response.status_code == 429
    assert response.json()["errors"]["code"] == "THROTTLED"


def test_status_rejects_other_methods(api_client):
    response = api_client.post(STATUS_URL, {}, format="json")

    assert response.status_code == 405
    assert response.json()["errors"]["code"] == "METHOD_NOT_ALLOWED"
