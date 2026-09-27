"""Health token verification and readiness checks.

Readiness reports check names and ``ok``/``error``/``skipped`` only; failure
details are logged server-side by exception type, never returned.
"""

from __future__ import annotations

import hmac
import logging
import uuid

from django.conf import settings
from django.core.cache import cache
from django.db import connections

from common.exceptions import ApplicationError

logger = logging.getLogger("apps.health")

OK = "ok"
ERROR = "error"
SKIPPED = "skipped"

HEALTH_TOKEN_HEADER = "X-Health-Check-Token"  # noqa: S105 - header name
HEALTH_TOKEN_QUERY_PARAM = "password"  # noqa: S105 - parameter name
READINESS_CACHE_PREFIX = "flash:readiness:"


class HealthTokenInvalid(ApplicationError):
    status_code = 401
    code = "HEALTH_TOKEN_INVALID"
    message = "Invalid health check password."


class ServiceNotReady(ApplicationError):
    status_code = 503
    code = "SERVICE_NOT_READY"
    message = "Service not ready."


def health_token_matches(provided: str | None) -> bool:
    """Constant-time comparison with ``HEALTH_CHECK_PASSWORD``; empty never matches."""
    expected = getattr(settings, "HEALTH_CHECK_PASSWORD", "") or ""
    if not expected or not provided:
        return False
    return hmac.compare_digest(provided.encode(), expected.encode())


def verify_health_token(request) -> None:
    """Accept the header (preferred) or ``?password=`` (DRF_SKILL compatibility)."""
    provided = request.headers.get(HEALTH_TOKEN_HEADER) or request.query_params.get(
        HEALTH_TOKEN_QUERY_PARAM
    )
    if not health_token_matches(provided):
        raise HealthTokenInvalid()


def check_database() -> str:
    try:
        with connections["default"].cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception as exc:  # noqa: BLE001 - any failure means "not ready"
        _log_failure("database", exc)
        return ERROR
    return OK


def check_cache() -> str:
    key = f"{READINESS_CACHE_PREFIX}{uuid.uuid4().hex}"
    try:
        cache.set(key, OK, timeout=30)
        value = cache.get(key)
        cache.delete(key)
    except Exception as exc:  # noqa: BLE001
        _log_failure("cache", exc)
        return ERROR
    if value != OK:
        logger.warning("Readiness check failed: cache (value not read back)")
        return ERROR
    return OK


def check_celery() -> str:
    """Broker reachability, only when Celery is enabled (ADR-017: skipped on the server)."""
    if not getattr(settings, "CELERY_ENABLED", False):
        return SKIPPED
    from config import celery_app

    if celery_app is None:
        logger.warning("Readiness check failed: celery (package not installed)")
        return ERROR
    try:
        with celery_app.connection_for_write() as connection:
            connection.ensure_connection(max_retries=1, interval_start=0, timeout=2)
    except Exception as exc:  # noqa: BLE001
        _log_failure("celery", exc)
        return ERROR
    return OK


CHECKS = {
    "database": check_database,
    "cache": check_cache,
    "celery": check_celery,
}


def run_readiness_checks() -> dict[str, str]:
    return {name: check() for name, check in CHECKS.items()}


def is_ready(checks: dict[str, str]) -> bool:
    return all(result in (OK, SKIPPED) for result in checks.values())


def _log_failure(name: str, exc: Exception) -> None:
    logger.warning("Readiness check failed: %s (%s)", name, type(exc).__name__)
