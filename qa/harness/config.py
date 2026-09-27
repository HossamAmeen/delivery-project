"""QA configuration, read from the environment only (TASK-008).

`make qa-remote` (ADR-018) exports:
- ``QA_BASE_URL``  = https://${API_DOMAIN}   (https://api.delivery.hossam-ameen.online)
- ``QA_WEB_URL``   = https://${WEB_DOMAIN}   (https://delivery.hossam-ameen.online)
- ``QA_HEALTH_TOKEN`` from shared/.env ``HEALTH_CHECK_PASSWORD``, into the pytest process only
- ``QA_<ROLE>_USERNAME`` / ``QA_<ROLE>_PASSWORD`` for CUSTOMER, DRIVER, STORE, ADMIN from
  /srv/flash/qa/credentials.env (written by `make seed-qa-users`)

Everything else has a default equal to the documented server configuration and may be
overridden with an env var when the server configuration changes. No secret has a default.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from urllib.parse import urlparse

from harness.secrets import Secret

ROLES = ("CUSTOMER", "DRIVER", "STORE", "ADMIN")

# Role -> PWA route area (ADR-011).
ROLE_AREAS = {"CUSTOMER": "/customer", "DRIVER": "/driver", "STORE": "/store", "ADMIN": "/admin"}


class ConfigError(RuntimeError):
    pass


def _env(name: str, default: str | None = None) -> str | None:
    value = os.environ.get(name)
    if value is None or value.strip() == "":
        return default
    return value.strip()


def parse_rate(rate: str) -> tuple[int, int]:
    """Parse a DRF rate such as ``10/minute`` into (requests, seconds)."""
    num, _, period = rate.partition("/")
    seconds = {"s": 1, "m": 60, "h": 3600, "d": 86400}[period.strip()[0].lower()]
    return int(num), seconds


@dataclass(frozen=True)
class RoleCredentials:
    role: str
    username: str
    password: Secret


@dataclass(frozen=True)
class QAConfig:
    base_url: str
    web_url: str
    deploy_path: str
    server_public_ip: str
    backend_port: int
    backend_service: str
    dental_service: str
    dental_urls: tuple[str, ...]
    cert_min_days: int
    releases_to_keep: int
    db_backups_to_keep: int
    min_free_disk_mb: int
    rate_anon: str
    rate_user: str
    rate_auth: str
    rate_health: str
    access_lifetime_min: int
    refresh_lifetime_days: int
    anon_throttle_path: str | None
    http_timeout: float

    @property
    def api_host(self) -> str:
        return urlparse(self.base_url).hostname or ""

    @property
    def web_host(self) -> str:
        return urlparse(self.web_url).hostname or ""

    # --- secrets: resolved lazily so --collect-only needs no env -------------------------
    def health_token(self) -> Secret:
        value = _env("QA_HEALTH_TOKEN")
        if not value:
            raise ConfigError(
                "QA_HEALTH_TOKEN is not set. It is exported by `make qa-remote` from the "
                "server's shared/.env; QA never runs locally (ADR-018)."
            )
        return Secret(value)

    def credentials(self, role: str) -> RoleCredentials:
        role = role.upper()
        user = _env(f"QA_{role}_USERNAME")
        pwd = _env(f"QA_{role}_PASSWORD")
        if not user or not pwd:
            raise ConfigError(
                f"QA_{role}_USERNAME / QA_{role}_PASSWORD are not set. Run `make seed-qa-users` "
                "on the server; `make qa-remote` loads /srv/flash/qa/credentials.env."
            )
        return RoleCredentials(role=role, username=user, password=Secret(pwd))

    def optional_credentials(self, prefix: str) -> RoleCredentials | None:
        """Optional extra users, e.g. QA_INACTIVE_USERNAME/PASSWORD. None when absent."""
        user = _env(f"QA_{prefix}_USERNAME")
        pwd = _env(f"QA_{prefix}_PASSWORD")
        if not user or not pwd:
            return None
        return RoleCredentials(role=prefix, username=user, password=Secret(pwd))


@lru_cache(maxsize=1)
def load() -> QAConfig:
    base_url = (_env("QA_BASE_URL", "https://api.delivery.hossam-ameen.online") or "").rstrip("/")
    web_url = (_env("QA_WEB_URL", "https://delivery.hossam-ameen.online") or "").rstrip("/")
    for name, url in (("QA_BASE_URL", base_url), ("QA_WEB_URL", web_url)):
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.hostname in {"localhost", "127.0.0.1", "::1"}:
            raise ConfigError(
                f"{name} must be the deployed public HTTPS URL (ADR-018), got a non-HTTPS or local URL."
            )
    return QAConfig(
        base_url=base_url,
        web_url=web_url,
        deploy_path=_env("QA_DEPLOY_PATH", "/srv/flash") or "/srv/flash",
        server_public_ip=_env("QA_SERVER_PUBLIC_IP", "34.123.215.195") or "",
        backend_port=int(_env("QA_BACKEND_PORT", "8010") or 8010),
        backend_service=_env("QA_BACKEND_SERVICE", "flash-backend") or "flash-backend",
        dental_service=_env("QA_DENTAL_SERVICE", "dental-clinic-backend") or "",
        dental_urls=tuple(
            u.strip()
            for u in (
                _env(
                    "QA_DENTAL_URLS",
                    "https://dental.hossam-ameen.online/,https://api.dental.hossam-ameen.online/",
                )
                or ""
            ).split(",")
            if u.strip()
        ),
        cert_min_days=int(_env("QA_CERT_MIN_DAYS", "60") or 60),
        releases_to_keep=int(_env("QA_RELEASES_TO_KEEP", "5") or 5),
        db_backups_to_keep=int(_env("QA_DB_BACKUPS_TO_KEEP", "5") or 5),
        min_free_disk_mb=int(_env("QA_MIN_FREE_DISK_MB", "1500") or 1500),
        rate_anon=_env("QA_RATELIMIT_ANON", "60/minute") or "60/minute",
        rate_user=_env("QA_RATELIMIT_USER", "300/minute") or "300/minute",
        rate_auth=_env("QA_RATELIMIT_AUTH", "10/minute") or "10/minute",
        rate_health=_env("QA_RATELIMIT_HEALTH", "120/minute") or "120/minute",
        access_lifetime_min=int(_env("QA_JWT_ACCESS_LIFETIME_MINUTES", "30") or 30),
        refresh_lifetime_days=int(_env("QA_JWT_REFRESH_LIFETIME_DAYS", "7") or 7),
        anon_throttle_path=_env("QA_ANON_THROTTLE_PATH"),
        http_timeout=float(_env("QA_HTTP_TIMEOUT", "20") or 20),
    )
