"""Fixtures for project-level tests."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import ModuleType

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
ENV_EXAMPLE = BACKEND_DIR / ".env.example"

# Variables that influence settings but are not listed in .env.example.
EXTRA_SETTINGS_VARS = ("DJANGO_ENV_FILE",)


def parse_env_file(path: Path) -> dict[str, str]:
    """Parse a simple KEY=VALUE env file (comments and blank lines skipped)."""
    values: dict[str, str] = {}
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def managed_env_keys() -> set[str]:
    """Every variable documented in .env.example (commented ones included)."""
    keys = set(parse_env_file(ENV_EXAMPLE))
    for raw in ENV_EXAMPLE.read_text().splitlines():
        line = raw.strip().lstrip("#").strip()
        if "=" in line and line.split("=", 1)[0].isupper():
            keys.add(line.split("=", 1)[0])
    return keys | set(EXTRA_SETTINGS_VARS)


@pytest.fixture
def server_env(tmp_path) -> dict[str, str]:
    """Server-like production environment (ADR-015/017) with dummy secrets."""
    return {
        "SECRET_KEY": "dummy-server-like-secret-key-9f8e7d6c5b4a3210-fedcba9876543210-xyz",
        "ALLOWED_HOSTS": "api.delivery.example.test,127.0.0.1,localhost",
        "DATABASE_URL": f"sqlite:///{tmp_path / 'db' / 'flash.sqlite3'}",
        "STATIC_ROOT": str(tmp_path / "static"),
        "MEDIA_ROOT": str(tmp_path / "media"),
        "CORS_ALLOWED_ORIGINS": "https://delivery.example.test",
        "CSRF_TRUSTED_ORIGINS": "https://api.delivery.example.test,https://delivery.example.test",
        "SECURE_PROXY_SSL_HEADER": "HTTP_X_FORWARDED_PROTO,https",
        "NUM_PROXIES": "1",
        "HEALTH_CHECK_PASSWORD": "dummy-server-like-health-token",
        "RATELIMIT_CACHE_URL": f"filecache://{tmp_path / 'cache'}",
        "CELERY_ENABLED": "False",
    }


@pytest.fixture
def load_settings(monkeypatch, tmp_path):
    """Import a fresh copy of ``config.settings.<name>`` under a given environment.

    The running Django settings are not touched: the fresh modules are removed
    from ``sys.modules`` again and the originals restored afterwards.
    """
    import config.settings as settings_pkg

    def _load(name: str, env: dict[str, str]) -> ModuleType:
        for key in managed_env_keys():
            monkeypatch.delenv(key, raising=False)
        monkeypatch.setenv("DJANGO_ENV_FILE", str(tmp_path / "no-such.env"))
        for key, value in env.items():
            monkeypatch.setenv(key, value)

        module_names = ["config.settings.base", f"config.settings.{name}"]
        saved = {module: sys.modules.pop(module, None) for module in module_names}
        saved_attrs = {
            module: getattr(settings_pkg, module.rsplit(".", 1)[1], None) for module in module_names
        }
        try:
            return importlib.import_module(f"config.settings.{name}")
        finally:
            for module, original in saved.items():
                attr = module.rsplit(".", 1)[1]
                if original is None:
                    sys.modules.pop(module, None)
                else:
                    sys.modules[module] = original
                if saved_attrs[module] is not None:
                    setattr(settings_pkg, attr, saved_attrs[module])

    return _load
