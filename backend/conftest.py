"""Global pytest fixtures (visible to tests/, common/ and apps/)."""

from __future__ import annotations

import pytest
from django.core.cache import caches
from rest_framework.test import APIClient

TEST_PASSWORD = "Str0ng-test-passw0rd!"  # noqa: S105 - test-only credential


@pytest.fixture(autouse=True)
def _isolated_cache():
    """Every test starts with an empty cache (throttle counters included)."""
    for cache in caches.all():
        cache.clear()
    yield
    for cache in caches.all():
        cache.clear()


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def make_user(db, django_user_model):
    """Create a user; ``role`` defaults to CUSTOMER (tests only)."""

    def _make(username: str = "alice", password: str = TEST_PASSWORD, **fields):
        fields.setdefault("role", django_user_model.Role.CUSTOMER)
        return django_user_model.objects.create_user(username=username, password=password, **fields)

    return _make


@pytest.fixture
def user(make_user):
    return make_user()


@pytest.fixture
def auth_client(api_client, user) -> APIClient:
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def throttle_rates(settings):
    """Override DRF throttle rates, e.g. ``throttle_rates(anon="2/minute")``."""

    def _set(**rates: str) -> None:
        rest = dict(settings.REST_FRAMEWORK)
        rest["DEFAULT_THROTTLE_RATES"] = {**rest["DEFAULT_THROTTLE_RATES"], **rates}
        settings.REST_FRAMEWORK = rest

    return _set
