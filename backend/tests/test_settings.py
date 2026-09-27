"""Settings tests (TASK-001): env-driven configuration, SQLite pragmas, production safety."""

from __future__ import annotations

import logging
import os
import subprocess
import sys

import pytest
from django.core.exceptions import ImproperlyConfigured

from config.settings._helpers import (
    SQLITE_OPTIONS,
    build_database,
    parse_proxy_ssl_header,
    require_non_placeholder,
)

from .conftest import BACKEND_DIR, ENV_EXAMPLE, managed_env_keys, parse_env_file

EXPECTED_INIT_COMMAND = (
    "PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL; "
    "PRAGMA busy_timeout=20000; PRAGMA foreign_keys=ON;"
)


# --- Helpers -----------------------------------------------------------------


def test_sqlite_database_gets_wal_options_and_no_persistent_connections():
    config = build_database("sqlite:////tmp/flash-test.sqlite3", conn_max_age=600)

    assert config["ENGINE"] == "django.db.backends.sqlite3"
    assert config["NAME"] == "/tmp/flash-test.sqlite3"
    assert config["CONN_MAX_AGE"] == 0
    assert config["OPTIONS"]["timeout"] == 20
    assert config["OPTIONS"]["transaction_mode"] == "IMMEDIATE"
    assert config["OPTIONS"]["init_command"] == EXPECTED_INIT_COMMAND


def test_non_sqlite_database_gets_no_sqlite_options():
    config = build_database("postgres://flash:pw@db.example.test:5432/flash", conn_max_age=600)

    assert config["ENGINE"] == "django.db.backends.postgresql"
    assert config["CONN_MAX_AGE"] == 600
    options = config.get("OPTIONS", {})
    for key in SQLITE_OPTIONS:
        assert key not in options


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("HTTP_X_FORWARDED_PROTO,https", ("HTTP_X_FORWARDED_PROTO", "https")),
        (" HTTP_X_FORWARDED_PROTO , https ", ("HTTP_X_FORWARDED_PROTO", "https")),
        ("", None),
        ("   ", None),
        (None, None),
    ],
)
def test_parse_proxy_ssl_header(value, expected):
    assert parse_proxy_ssl_header(value) == expected


@pytest.mark.parametrize("value", ["HTTP_X_FORWARDED_PROTO", "a,b,c", ",https"])
def test_parse_proxy_ssl_header_rejects_malformed_values(value):
    with pytest.raises(ImproperlyConfigured):
        parse_proxy_ssl_header(value)


@pytest.mark.parametrize("value", ["", "  ", "change-me"])
def test_require_non_placeholder_rejects_empty_and_placeholder(value):
    with pytest.raises(ImproperlyConfigured) as excinfo:
        require_non_placeholder("SECRET_KEY", value, ("change-me",))
    # The error names the variable but never echoes its value.
    assert "SECRET_KEY" in str(excinfo.value)


# --- Development ---------------------------------------------------------------


def test_development_settings_load_with_env_example_values(load_settings):
    env = parse_env_file(ENV_EXAMPLE)
    env.pop("DJANGO_SETTINGS_MODULE", None)

    module = load_settings("development", env)

    assert module.DEBUG is True
    assert module.API_DOCS_PUBLIC is True
    assert module.SECRET_KEY == "change-me"
    assert module.ALLOWED_HOSTS == ["localhost", "127.0.0.1"]
    assert module.DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3"
    assert module.DATABASES["default"]["OPTIONS"]["init_command"] == EXPECTED_INIT_COMMAND
    assert module.SECURE_PROXY_SSL_HEADER is None
    assert module.STATIC_URL == "/static/"
    assert module.MEDIA_URL == "/media/"
    assert module.TIME_ZONE == "UTC"


def test_settings_require_secret_key_everywhere(load_settings):
    env = parse_env_file(ENV_EXAMPLE)
    env.pop("SECRET_KEY")
    env.pop("DJANGO_SETTINGS_MODULE", None)

    with pytest.raises(ImproperlyConfigured):
        load_settings("development", env)


def test_env_example_documents_every_variable_read_by_settings():
    documented = managed_env_keys()
    required = {
        "SECRET_KEY",
        "DEBUG",
        "ALLOWED_HOSTS",
        "DATABASE_URL",
        "STATIC_ROOT",
        "MEDIA_ROOT",
        "CORS_ALLOWED_ORIGINS",
        "CSRF_TRUSTED_ORIGINS",
        "SECURE_PROXY_SSL_HEADER",
        "SECURE_SSL_REDIRECT",
        "SECURE_HSTS_SECONDS",
        "API_DOCS_PUBLIC",
        "LOG_LEVEL",
        "TIME_ZONE",
        "LANGUAGE_CODE",
        # DRF_SKILL §8 and §78
        "JWT_ACCESS_TOKEN_LIFETIME_MINUTES",
        "JWT_REFRESH_TOKEN_LIFETIME_DAYS",
        "HEALTH_CHECK_PASSWORD",
        "CELERY_ENABLED",
        "CELERY_BEAT_ENABLED",
        "CELERY_BROKER_URL",
        "CELERY_RESULT_BACKEND",
        "CELERY_TASK_ALWAYS_EAGER",
        "CELERY_TASK_EAGER_PROPAGATES",
        "CELERY_WORKER_CONCURRENCY",
        "DOMAIN",
        "BACKEND_PORT",
        "FRONTEND_PORT",
        "BACKEND_PATH",
        "FRONTEND_PATH",
        "MEDIA_PATH",
        "STATIC_PATH",
        "SYSTEMD_SERVICE_NAME",
        "RATELIMIT_ANON",
        "RATELIMIT_USER",
        "RATELIMIT_AUTH",
        "RATELIMIT_SENSITIVE",
        "RATELIMIT_HEALTH",
        "RATELIMIT_CACHE_URL",
        "NUM_PROXIES",
    }
    assert required <= documented, sorted(required - documented)


# --- Production ----------------------------------------------------------------


def test_production_settings_are_secure_with_server_like_env(load_settings, server_env):
    module = load_settings("production", server_env)

    assert module.DEBUG is False
    assert module.SESSION_COOKIE_SECURE is True
    assert module.CSRF_COOKIE_SECURE is True
    assert module.SECURE_SSL_REDIRECT is False
    assert module.SECURE_HSTS_SECONDS == 0
    assert module.SECURE_PROXY_SSL_HEADER == ("HTTP_X_FORWARDED_PROTO", "https")
    assert module.API_DOCS_PUBLIC is False
    assert module.ALLOWED_HOSTS == ["api.delivery.example.test", "127.0.0.1", "localhost"]
    assert module.CORS_ALLOWED_ORIGINS == ["https://delivery.example.test"]
    assert module.CSRF_TRUSTED_ORIGINS == [
        "https://api.delivery.example.test",
        "https://delivery.example.test",
    ]
    assert str(module.STATIC_ROOT) == server_env["STATIC_ROOT"]
    assert str(module.MEDIA_ROOT) == server_env["MEDIA_ROOT"]
    database = module.DATABASES["default"]
    assert database["OPTIONS"]["transaction_mode"] == "IMMEDIATE"
    assert database["CONN_MAX_AGE"] == 0


def test_production_forces_debug_off(load_settings, server_env):
    module = load_settings("production", {**server_env, "DEBUG": "True"})

    assert module.DEBUG is False


def test_production_hsts_and_redirect_are_configurable(load_settings, server_env):
    module = load_settings(
        "production",
        {**server_env, "SECURE_HSTS_SECONDS": "3600", "SECURE_SSL_REDIRECT": "True"},
    )

    assert module.SECURE_HSTS_SECONDS == 3600
    assert module.SECURE_SSL_REDIRECT is True


def test_production_refuses_to_start_without_secret_key(load_settings, server_env):
    env = dict(server_env)
    env.pop("SECRET_KEY")

    with pytest.raises(ImproperlyConfigured):
        load_settings("production", env)


@pytest.mark.parametrize("variable", ["SECRET_KEY", "HEALTH_CHECK_PASSWORD"])
def test_production_refuses_placeholder_secrets(load_settings, server_env, variable):
    with pytest.raises(ImproperlyConfigured):
        load_settings("production", {**server_env, variable: "change-me"})


@pytest.mark.parametrize(
    "missing",
    ["ALLOWED_HOSTS", "DATABASE_URL", "STATIC_ROOT", "MEDIA_ROOT", "HEALTH_CHECK_PASSWORD"],
)
def test_production_requires_server_values(load_settings, server_env, missing):
    env = dict(server_env)
    env.pop(missing)

    with pytest.raises(ImproperlyConfigured):
        load_settings("production", env)


def test_check_deploy_with_server_like_env_has_no_errors(server_env):
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in managed_env_keys() and key != "DJANGO_SETTINGS_MODULE"
    }
    env.update(server_env)
    env["DJANGO_SETTINGS_MODULE"] = "config.settings.production"
    env["DJANGO_ENV_FILE"] = str(BACKEND_DIR / "no-such.env")

    result = subprocess.run(  # noqa: S603 - fixed argv, test-only
        [sys.executable, "manage.py", "check", "--deploy", "--fail-level", "ERROR"],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert server_env["SECRET_KEY"] not in result.stdout + result.stderr
    assert server_env["HEALTH_CHECK_PASSWORD"] not in result.stdout + result.stderr


# --- Logging / CORS -------------------------------------------------------------


def _application_handlers(logger: logging.Logger) -> list[logging.Handler]:
    """Handlers installed by the app's LOGGING config.

    pytest's logging plugin attaches its own capture/report handlers (one is a
    FileHandler on os.devnull) to the root logger during the run; they are not
    part of the application configuration, so they are excluded by module.
    """
    return [h for h in logger.handlers if not type(h).__module__.startswith("_pytest")]


def test_logging_writes_to_stream_handlers_only(settings):
    # 1. The configuration declares stream handlers only, with no file target.
    handlers = settings.LOGGING["handlers"]
    assert handlers
    for handler in handlers.values():
        assert handler["class"] == "logging.StreamHandler"
        assert "filename" not in handler
        assert "stream" not in handler  # default stream = stderr

    # 2. What Django actually installed from it: stream handlers, never files.
    installed = _application_handlers(logging.getLogger()) + _application_handlers(
        logging.getLogger("django")
    )
    assert installed
    for handler in installed:
        assert type(handler) is logging.StreamHandler
        assert not isinstance(handler, logging.FileHandler)


def test_cors_preflight_allows_configured_origin(client, settings):
    settings.CORS_ALLOWED_ORIGINS = ["https://delivery.example.test"]

    response = client.options(
        "/api/status/",
        HTTP_ORIGIN="https://delivery.example.test",
        HTTP_ACCESS_CONTROL_REQUEST_METHOD="GET",
    )

    assert response["access-control-allow-origin"] == "https://delivery.example.test"
    assert "access-control-allow-credentials" not in response


def test_cors_preflight_ignores_other_origins(client, settings):
    settings.CORS_ALLOWED_ORIGINS = ["https://delivery.example.test"]

    response = client.options(
        "/api/status/",
        HTTP_ORIGIN="https://evil.example.test",
        HTTP_ACCESS_CONTROL_REQUEST_METHOD="GET",
    )

    assert "access-control-allow-origin" not in response


@pytest.mark.django_db
def test_cors_exposes_retry_after_to_the_pwa(client, settings):
    """The PWA must read Retry-After on cross-origin 429 responses (TASK-007)."""
    settings.CORS_ALLOWED_ORIGINS = ["https://delivery.example.test"]

    response = client.get("/api/status/", HTTP_ORIGIN="https://delivery.example.test")

    assert response["access-control-allow-origin"] == "https://delivery.example.test"
    assert "retry-after" in response["access-control-expose-headers"].lower()
