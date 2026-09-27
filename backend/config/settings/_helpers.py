"""Pure helpers used by the settings modules.

They take plain values and return plain settings structures, so each rule
(SQLite pragmas, proxy header parsing, cache URL policy, Celery toggle) can be
unit-tested without reloading Django.
"""

from __future__ import annotations

from typing import NamedTuple

import dj_database_url
import environ
from django.core.exceptions import ImproperlyConfigured

SQLITE_ENGINE = "django.db.backends.sqlite3"

# ADR-017: WAL for concurrent reads with several gunicorn workers, IMMEDIATE
# transactions to avoid lock-upgrade deadlocks, and a busy timeout.
SQLITE_OPTIONS = {
    "timeout": 20,
    "transaction_mode": "IMMEDIATE",
    "init_command": (
        "PRAGMA journal_mode=WAL; "
        "PRAGMA synchronous=NORMAL; "
        "PRAGMA busy_timeout=20000; "
        "PRAGMA foreign_keys=ON;"
    ),
}


class FlashEnv(environ.Env):
    """``environ.Env`` that also accepts ``locmem://`` as a cache URL.

    django-environ only knows ``locmemcache://``; ADR-017/ADR-018 use the
    shorter ``locmem://`` spelling, so both are accepted.
    """

    CACHE_SCHEMES = {
        **environ.Env.CACHE_SCHEMES,
        "locmem": "django.core.cache.backends.locmem.LocMemCache",
    }


def build_database(url: str, conn_max_age: int = 600) -> dict:
    """Return a ``DATABASES`` entry for ``url``.

    For SQLite the ADR-017 options are applied and persistent connections are
    disabled (``CONN_MAX_AGE=0``). Other engines are left untouched.
    """
    config = dj_database_url.parse(url, conn_max_age=conn_max_age)
    if config["ENGINE"] == SQLITE_ENGINE:
        config["CONN_MAX_AGE"] = 0
        config["OPTIONS"] = {**config.get("OPTIONS", {}), **SQLITE_OPTIONS}
    return config


def parse_proxy_ssl_header(value: str | None) -> tuple[str, str] | None:
    """Parse ``SECURE_PROXY_SSL_HEADER`` (``"HTTP_X_FORWARDED_PROTO,https"``).

    An empty or missing value means "no trusted proxy header" (``None``).
    """
    if not value or not value.strip():
        return None
    parts = [part.strip() for part in value.split(",")]
    if len(parts) != 2 or not all(parts):
        raise ImproperlyConfigured(
            "SECURE_PROXY_SSL_HEADER must look like 'HTTP_X_FORWARDED_PROTO,https'."
        )
    return parts[0], parts[1]


def require_non_placeholder(name: str, value: str, placeholders: tuple[str, ...]) -> str:
    """Fail fast when a required secret is empty or still a documented placeholder."""
    if not value or not value.strip() or value.strip() in placeholders:
        raise ImproperlyConfigured(f"Set a real value for the {name} environment variable.")
    return value


def parse_optional_int(value: str | None) -> int | None:
    """``""``/unset → ``None``; otherwise a non-negative integer."""
    if value is None or not value.strip():
        return None
    try:
        number = int(value)
    except ValueError as exc:
        raise ImproperlyConfigured(f"Expected an integer, got {value!r}.") from exc
    if number < 0:
        raise ImproperlyConfigured(f"Expected a non-negative integer, got {value!r}.")
    return number


LOCMEM_BACKEND = "django.core.cache.backends.locmem.LocMemCache"
FILE_BACKEND = "django.core.cache.backends.filebased.FileBasedCache"
FILE_CACHE_MAX_ENTRIES = 10000


def build_cache(url: str | None, *, production: bool) -> dict:
    """Return ``CACHES["default"]`` for ``RATELIMIT_CACHE_URL`` (ADR-017).

    Accepts ``locmem://``, ``filecache:///abs/path`` and ``redis://...``.
    Production refuses a missing URL and LocMem: several gunicorn workers
    would each keep their own throttle counters.
    """
    if not url or not url.strip():
        if production:
            raise ImproperlyConfigured(
                "RATELIMIT_CACHE_URL is required in production "
                "(e.g. filecache:///srv/flash/shared/cache)."
            )
        url = "locmem://"
    config = FlashEnv.cache_url_config(url.strip())
    backend = config["BACKEND"]
    if production and backend == LOCMEM_BACKEND:
        raise ImproperlyConfigured(
            "RATELIMIT_CACHE_URL must be a shared cache in production, not locmem://."
        )
    if backend == FILE_BACKEND:
        location = str(config.get("LOCATION", ""))
        if not location.startswith("/"):
            raise ImproperlyConfigured(
                "RATELIMIT_CACHE_URL filecache:// needs an absolute path (filecache:///abs/path)."
            )
        config["OPTIONS"] = {**config.get("OPTIONS", {}), "MAX_ENTRIES": FILE_CACHE_MAX_ENTRIES}
    return config


class CeleryRuntime(NamedTuple):
    broker_url: str
    result_backend: str | None
    always_eager: bool


def celery_runtime(
    *, enabled: bool, broker_url: str, result_backend: str, always_eager: bool
) -> CeleryRuntime:
    """Effective Celery transport settings for the ``CELERY_ENABLED`` toggle.

    Disabled (the server, ADR-017): tasks run inline (eager) and the broker is
    the in-memory transport, so nothing ever connects to Redis. Enabled: the
    configured broker/result backend are used unchanged.
    """
    if not enabled:
        return CeleryRuntime(broker_url="memory://", result_backend=None, always_eager=True)
    return CeleryRuntime(
        broker_url=broker_url, result_backend=result_backend, always_eager=always_eager
    )
