"""Settings for the pytest suite (development + isolated test values).

The server runner (ADR-018) exports DATABASE_URL, SECRET_KEY, etc.; they are
still read here. Only values that must be isolated for tests are overridden.
"""

import os

# A dummy key keeps the suite self-contained; the runner may export its own.
os.environ.setdefault("SECRET_KEY", "test-only-insecure-key-0123456789-abcdefghijklmnopqrstuvwxyz")

from .development import *  # noqa: E402, F403

DEBUG = False

# Fast hashing for tests only.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# DRF_SKILL §77: isolated test cache, never the server cache or Redis.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "flash-tests",
    }
}

# Deterministic JSON-only rendering; the test-only app for common/ tests.
REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    "DEFAULT_RENDERER_CLASSES": ["common.renderers.EnvelopeJSONRenderer"],
}
INSTALLED_APPS = [*INSTALLED_APPS, "tests.testapp"]
