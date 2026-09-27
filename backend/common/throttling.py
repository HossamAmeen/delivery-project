"""Throttle classes (DRF_SKILL §61-75).

The DRF classes bind ``THROTTLE_RATES`` once at import time; these subclasses
read the rate from ``api_settings`` on every request, so the env-configured
rates and test overrides always apply.
"""

from __future__ import annotations

from django.core.exceptions import ImproperlyConfigured
from rest_framework import throttling
from rest_framework.settings import api_settings


class _SettingsRateMixin:
    scope: str | None

    def get_rate(self) -> str | None:
        rates = api_settings.DEFAULT_THROTTLE_RATES
        try:
            return rates[self.scope]
        except KeyError as exc:
            raise ImproperlyConfigured(
                f"No default throttle rate set for '{self.scope}' scope"
            ) from exc

    def get_ident(self, request) -> str | None:
        # DRF trusts X-Forwarded-For entirely when NUM_PROXIES is None, which a
        # client can spoof (DRF_SKILL §74). Without an explicitly configured
        # proxy count, use the socket address only.
        if api_settings.NUM_PROXIES is None:
            return request.META.get("REMOTE_ADDR")
        return super().get_ident(request)


class AnonRateThrottle(_SettingsRateMixin, throttling.AnonRateThrottle):
    """Unauthenticated requests, keyed by client IP (``anon`` scope)."""


class UserRateThrottle(_SettingsRateMixin, throttling.UserRateThrottle):
    """Authenticated requests keyed by user id; anonymous by IP (``user`` scope)."""


class AuthRateThrottle(UserRateThrottle):
    """Login/refresh endpoints: stricter than normal APIs (§66)."""

    scope = "auth"


class SensitiveRateThrottle(UserRateThrottle):
    """Sensitive operations (§67)."""

    scope = "sensitive"


class HealthRateThrottle(UserRateThrottle):
    """Health/status endpoints: own scope so deploy checks are not starved (§75)."""

    scope = "health"
