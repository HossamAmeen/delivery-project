"""Production settings (the shared VPS, ADR-015).

DEBUG is always off. Values that must be set on the server have no default,
so a missing variable stops the process at start-up (fail fast).
"""

from pathlib import Path

from ._helpers import build_cache, build_database, require_non_placeholder
from .base import *  # noqa: F403
from .base import env

PLACEHOLDERS = ("change-me", "changeme")

DEBUG = False

SECRET_KEY = require_non_placeholder("SECRET_KEY", env.str("SECRET_KEY"), PLACEHOLDERS)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")

DATABASES = {
    "default": build_database(
        env.str("DATABASE_URL"),
        conn_max_age=env.int("DB_CONN_MAX_AGE", default=600),
    )
}

# Shared by all gunicorn workers; LocMem is refused (ADR-017).
CACHES = {"default": build_cache(env.str("RATELIMIT_CACHE_URL", default=""), production=True)}

STATIC_ROOT = Path(env.str("STATIC_ROOT"))
MEDIA_ROOT = Path(env.str("MEDIA_ROOT"))

# nginx redirects to HTTPS and sets HSTS (ADR-015), so both stay configurable
# and default off here; cookies are always secure.
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=False)
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=0)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True

API_DOCS_PUBLIC = env.bool("API_DOCS_PUBLIC", default=False)

# No default: fail fast when missing (TASK-004).
HEALTH_CHECK_PASSWORD = require_non_placeholder(
    "HEALTH_CHECK_PASSWORD", env.str("HEALTH_CHECK_PASSWORD"), PLACEHOLDERS
)
