"""Flash backend project configuration.

Celery is optional: production does not install it while CELERY_ENABLED=False
(ADR-017), so a missing ``celery`` package is tolerated. Any other import error
still raises.
"""

try:
    from .celery import app as celery_app
except ModuleNotFoundError as exc:  # pragma: no cover - exercised in a subprocess test
    if exc.name != "celery" and not str(exc.name).startswith("celery."):
        raise
    celery_app = None

__all__ = ("celery_app",)
