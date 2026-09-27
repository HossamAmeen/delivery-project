"""Cache and optional Celery configuration (TASK-005, ADR-017)."""

from __future__ import annotations

import os
import subprocess
import sys
from types import SimpleNamespace

import pytest
from django.contrib.auth.models import AnonymousUser
from django.core.cache.backends.filebased import FileBasedCache
from django.core.exceptions import ImproperlyConfigured

from common.throttling import AnonRateThrottle
from config.settings._helpers import (
    FILE_BACKEND,
    LOCMEM_BACKEND,
    build_cache,
    celery_runtime,
)

from .conftest import BACKEND_DIR, ENV_EXAMPLE, parse_env_file

REDIS_BACKEND = "django.core.cache.backends.redis.RedisCache"


# --- Cache URL -----------------------------------------------------------------


@pytest.mark.parametrize("url", ["locmem://", "locmemcache://", "", None])
def test_locmem_and_missing_url_give_locmem_outside_production(url):
    assert build_cache(url, production=False)["BACKEND"] == LOCMEM_BACKEND


def test_filecache_url_gives_file_based_cache_with_max_entries(tmp_path):
    config = build_cache(f"filecache://{tmp_path}/cache", production=False)

    assert config["BACKEND"] == FILE_BACKEND
    assert config["LOCATION"] == f"{tmp_path}/cache"
    assert config["OPTIONS"]["MAX_ENTRIES"] == 10000


def test_filecache_requires_absolute_path():
    with pytest.raises(ImproperlyConfigured):
        build_cache("filecache://relative/cache", production=False)


def test_redis_url_is_supported_for_later():
    config = build_cache("redis://localhost:6379/2", production=True)

    assert config["BACKEND"] == REDIS_BACKEND
    assert config["LOCATION"] == "redis://localhost:6379/2"


@pytest.mark.parametrize("url", ["locmem://", "locmemcache://", "", None])
def test_production_refuses_locmem_or_missing_cache_url(url):
    with pytest.raises(ImproperlyConfigured):
        build_cache(url, production=True)


def test_production_accepts_filecache(tmp_path):
    config = build_cache(f"filecache://{tmp_path}", production=True)

    assert config["BACKEND"] == FILE_BACKEND


def test_development_settings_default_to_locmem(load_settings):
    env = parse_env_file(ENV_EXAMPLE)
    env.pop("RATELIMIT_CACHE_URL")

    module = load_settings("development", env)

    assert module.CACHES["default"]["BACKEND"] == LOCMEM_BACKEND


def test_production_settings_use_server_filecache(load_settings, server_env):
    module = load_settings("production", server_env)

    assert module.CACHES["default"]["BACKEND"] == FILE_BACKEND
    assert module.CACHES["default"]["OPTIONS"]["MAX_ENTRIES"] == 10000
    assert module.REST_FRAMEWORK["NUM_PROXIES"] == 1


@pytest.mark.parametrize("value", ["locmem://", None])
def test_production_settings_refuse_locmem_or_missing_cache(load_settings, server_env, value):
    env = dict(server_env)
    if value is None:
        env.pop("RATELIMIT_CACHE_URL")
    else:
        env["RATELIMIT_CACHE_URL"] = value

    with pytest.raises(ImproperlyConfigured):
        load_settings("production", env)


def test_num_proxies_unset_locally(load_settings):
    env = parse_env_file(ENV_EXAMPLE)

    module = load_settings("development", env)

    assert module.REST_FRAMEWORK["NUM_PROXIES"] is None


def test_invalid_num_proxies_is_rejected(load_settings):
    env = {**parse_env_file(ENV_EXAMPLE), "NUM_PROXIES": "one"}

    with pytest.raises(ImproperlyConfigured):
        load_settings("development", env)


@pytest.mark.ratelimit
def test_file_cache_throttle_counters_are_shared_between_workers(tmp_path, throttle_rates):
    """Two FileBasedCache instances on one directory = two gunicorn workers."""
    throttle_rates(anon="2/minute")
    location = str(tmp_path / "cache")
    worker_a = FileBasedCache(location, {})
    worker_b = FileBasedCache(location, {})
    request = SimpleNamespace(user=AnonymousUser(), META={"REMOTE_ADDR": "198.51.100.7"})

    def allowed(cache) -> bool:
        throttle = AnonRateThrottle()
        throttle.cache = cache
        return throttle.allow_request(request, view=None)

    assert allowed(worker_a) is True
    assert allowed(worker_b) is True
    # The third request is refused whichever worker receives it.
    assert allowed(worker_a) is False
    assert allowed(worker_b) is False


# --- Celery toggle -----------------------------------------------------------------


def test_celery_disabled_runs_inline_without_a_broker():
    runtime = celery_runtime(
        enabled=False,
        broker_url="redis://localhost:6379/0",
        result_backend="redis://localhost:6379/1",
        always_eager=False,
    )

    assert runtime.broker_url == "memory://"
    assert runtime.result_backend is None
    assert runtime.always_eager is True


def test_celery_enabled_uses_configured_broker():
    runtime = celery_runtime(
        enabled=True,
        broker_url="redis://localhost:6379/0",
        result_backend="redis://localhost:6379/1",
        always_eager=False,
    )

    assert runtime.broker_url == "redis://localhost:6379/0"
    assert runtime.result_backend == "redis://localhost:6379/1"
    assert runtime.always_eager is False


@pytest.mark.parametrize(
    ("enabled", "expected_broker"),
    [("False", "memory://"), ("True", "redis://broker.example.test:6379/0")],
)
def test_settings_for_both_celery_states(load_settings, enabled, expected_broker):
    env = {
        **parse_env_file(ENV_EXAMPLE),
        "CELERY_ENABLED": enabled,
        "CELERY_BEAT_ENABLED": "True",
        "CELERY_BROKER_URL": "redis://broker.example.test:6379/0",
    }

    module = load_settings("development", env)

    assert module.CELERY_ENABLED is (enabled == "True")
    assert module.CELERY_BROKER_URL == expected_broker
    # Beat can only be on when Celery itself is on.
    assert module.CELERY_BEAT_ENABLED is (enabled == "True")


def test_test_settings_run_with_celery_disabled_and_no_redis(settings):
    assert settings.CELERY_ENABLED is False
    assert "redis" not in settings.CELERY_BROKER_URL
    assert "redis" not in str(settings.CACHES["default"]["BACKEND"]).lower()


def test_celery_task_runs_eagerly_through_the_app():
    celery = pytest.importorskip("celery")
    from config import celery_app

    assert celery_app is not None

    @celery.shared_task
    def add(x, y):
        return x + y

    result = add.delay(2, 3)

    assert result.get(timeout=1) == 5
    assert celery_app.conf.task_always_eager is True
    assert celery_app.conf.broker_url == "memory://"


def test_config_imports_without_celery_installed():
    env = {k: v for k, v in os.environ.items() if k != "DJANGO_SETTINGS_MODULE"}
    code = "import sys; sys.modules['celery'] = None; import config; print(config.celery_app)"

    result = subprocess.run(  # noqa: S603 - fixed argv, test-only
        [sys.executable, "-c", code],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "None"
