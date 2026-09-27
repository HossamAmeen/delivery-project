"""Settings shared by every environment.

Every configurable value comes from the environment (DRF_SKILL §7-8). A
``backend/.env`` file is read only when it exists; on the server systemd
provides the environment from ``shared/.env`` (ADR-015).
Environment-specific overrides live in ``development.py`` and ``production.py``.
"""

from datetime import timedelta
from pathlib import Path

from ._helpers import (
    FlashEnv,
    build_cache,
    build_database,
    celery_runtime,
    parse_optional_int,
    parse_proxy_ssl_header,
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = FlashEnv()

# Optional local env file. DJANGO_ENV_FILE may point elsewhere (tests point it
# at a missing path so a developer's .env never leaks into settings tests).
ENV_FILE = Path(env.str("DJANGO_ENV_FILE", default=str(BASE_DIR / ".env")))
if ENV_FILE.is_file():
    FlashEnv.read_env(str(ENV_FILE), overwrite=False)

# --- Core ---
SECRET_KEY = env.str("SECRET_KEY")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

INSTALLED_APPS = [
    # Jazzmin must come before django.contrib.admin (DRF_SKILL §22).
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third party
    "corsheaders",
    "rest_framework",
    "drf_spectacular",
    # Project
    "common",
    "apps.users",
    "apps.health",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    # django-cors-headers: as high as possible, before CommonMiddleware.
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# --- Database ---
# DATABASE_URL via dj-database-url; SQLite gets the ADR-017 pragmas.
DATABASES = {
    "default": build_database(
        env.str("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
        conn_max_age=env.int("DB_CONN_MAX_AGE", default=600),
    )
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Auth ---
# Custom user from the first migration (ADR-003).
AUTH_USER_MODEL = "users.User"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- Internationalization ---
# Neutral defaults; final values pending BLK-009.
LANGUAGE_CODE = env.str("LANGUAGE_CODE", default="en")
TIME_ZONE = env.str("TIME_ZONE", default="UTC")
USE_I18N = True
USE_TZ = True

# --- Static / media ---
# nginx serves both directories on the server (ADR-015).
STATIC_URL = "/static/"
MEDIA_URL = "/media/"
STATIC_ROOT = Path(env.str("STATIC_ROOT", default=str(BASE_DIR / "staticfiles")))
MEDIA_ROOT = Path(env.str("MEDIA_ROOT", default=str(BASE_DIR / "media")))

# --- CORS/Proxy ---
# The PWA and the API are different origins (ADR-008). Auth uses the
# Authorization header, so no credentialed CORS.
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])
CORS_ALLOW_CREDENTIALS = False
CORS_EXPOSE_HEADERS = ["Retry-After"]
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])
# nginx is the single trusted hop and sets X-Forwarded-Proto (ADR-015).
SECURE_PROXY_SSL_HEADER = parse_proxy_ssl_header(env.str("SECURE_PROXY_SSL_HEADER", default=""))
USE_X_FORWARDED_HOST = False

# --- Security ---
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=False)
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=0)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", default=False)
SECURE_HSTS_PRELOAD = env.bool("SECURE_HSTS_PRELOAD", default=False)
SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", default=False)
CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE", default=False)
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

# --- Logging ---
# stdout/stderr only (journald on the server). Django's request loggers log
# the path, never the query string, so a ?password= health token is not logged.
LOG_LEVEL = env.str("LOG_LEVEL", default="INFO").upper()
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {"format": "%(asctime)s %(levelname)s %(name)s %(message)s"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "standard"},
    },
    "root": {"handlers": ["console"], "level": LOG_LEVEL},
    "loggers": {
        "django": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
    },
}

# --- API docs ---
# ADR-019: public in development, staff-only in production (used by TASK-004).
API_DOCS_PUBLIC = env.bool("API_DOCS_PUBLIC", default=False)

# --- DRF ---
API_PAGE_SIZE = env.int("API_PAGE_SIZE", default=20)
API_MAX_PAGE_SIZE = env.int("API_MAX_PAGE_SIZE", default=100)

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_RENDERER_CLASSES": ["common.renderers.EnvelopeJSONRenderer"],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
    ],
    "EXCEPTION_HANDLER": "common.exception_handler.custom_exception_handler",
    "DEFAULT_PAGINATION_CLASS": "common.pagination.StandardPagination",
    "PAGE_SIZE": API_PAGE_SIZE,
    # Global throttling: every endpoint inherits it (DRF_SKILL §62).
    "DEFAULT_THROTTLE_CLASSES": [
        "common.throttling.AnonRateThrottle",
        "common.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": env.str("RATELIMIT_ANON", default="60/minute"),
        "user": env.str("RATELIMIT_USER", default="300/minute"),
        "auth": env.str("RATELIMIT_AUTH", default="10/minute"),
        "sensitive": env.str("RATELIMIT_SENSITIVE", default="30/minute"),
        "health": env.str("RATELIMIT_HEALTH", default="120/minute"),
    },
    # Trusted proxies for client-IP resolution (ADR-015): unset locally, 1 on
    # the server where nginx overwrites X-Forwarded-For.
    "NUM_PROXIES": parse_optional_int(env.str("NUM_PROXIES", default="")),
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
}

# --- Cache ---
# Throttle counters live here (ADR-017): locmem:// locally/tests,
# filecache:///srv/flash/shared/cache on the server, redis:// later.
CACHES = {
    "default": build_cache(env.str("RATELIMIT_CACHE_URL", default="locmem://"), production=False)
}

# --- Celery ---
# Optional (DRF_SKILL §28). Disabled on the server: no broker, no workers.
# Redis DB layout when enabled: 0 broker, 1 results, 2 throttle cache.
CELERY_ENABLED = env.bool("CELERY_ENABLED", default=False)
CELERY_BEAT_ENABLED = CELERY_ENABLED and env.bool("CELERY_BEAT_ENABLED", default=False)
_celery = celery_runtime(
    enabled=CELERY_ENABLED,
    broker_url=env.str("CELERY_BROKER_URL", default="redis://localhost:6379/0"),
    result_backend=env.str("CELERY_RESULT_BACKEND", default="redis://localhost:6379/1"),
    always_eager=env.bool("CELERY_TASK_ALWAYS_EAGER", default=False),
)
CELERY_BROKER_URL = _celery.broker_url
CELERY_RESULT_BACKEND = _celery.result_backend
CELERY_TASK_ALWAYS_EAGER = _celery.always_eager
CELERY_TASK_EAGER_PROPAGATES = env.bool("CELERY_TASK_EAGER_PROPAGATES", default=False)
CELERY_WORKER_CONCURRENCY = env.int("CELERY_WORKER_CONCURRENCY", default=2)
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]

# --- OpenAPI ---
REST_FRAMEWORK["DEFAULT_SCHEMA_CLASS"] = "drf_spectacular.openapi.AutoSchema"
SPECTACULAR_SETTINGS = {
    "TITLE": "Flash API",
    "DESCRIPTION": (
        "Flash delivery platform API. Every JSON response uses the standard envelope "
        "`{success, message, data}` / `{success, message, errors}`; clients branch on "
        "`errors.code`. Every endpoint may return 429 (`THROTTLED`)."
    ),
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SCHEMA_PATH_PREFIX": r"/api/",
    "ENUM_NAME_OVERRIDES": {
        "CheckResultEnum": "apps.health.serializers.CHECK_RESULT_CHOICES",
        "OptionalCheckResultEnum": "apps.health.serializers.OPTIONAL_CHECK_RESULT_CHOICES",
    },
    "POSTPROCESSING_HOOKS": [
        "drf_spectacular.hooks.postprocess_schema_enums",
        "common.openapi.envelope_postprocessing_hook",
    ],
}

# --- Jazzmin ---
# Generic admin branding only; no business coupling (DRF_SKILL §22).
JAZZMIN_SETTINGS = {
    "site_title": "Flash Admin",
    "site_header": "Flash",
    "site_brand": "Flash",
    "welcome_sign": "Welcome to the Flash administration panel",
    "copyright": "Flash",
    "show_sidebar": True,
    "navigation_expanded": True,
}

# --- Health ---
# Token for /api/health/ and /api/health/ready/ (DRF_SKILL §23-24). Empty means
# every request is rejected; production requires a real value.
HEALTH_CHECK_PASSWORD = env.str("HEALTH_CHECK_PASSWORD", default="")

# --- JWT ---
# Bearer access/refresh tokens (DRF_SKILL §17). No refresh rotation in the MVP.
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=env.int("JWT_ACCESS_TOKEN_LIFETIME_MINUTES", default=30)
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=env.int("JWT_REFRESH_TOKEN_LIFETIME_DAYS", default=7)),
    "ROTATE_REFRESH_TOKENS": env.bool("JWT_ROTATE_REFRESH_TOKENS", default=False),
    "BLACKLIST_AFTER_ROTATION": False,
    "UPDATE_LAST_LOGIN": False,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}
