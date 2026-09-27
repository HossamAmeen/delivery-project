import pytest

HEALTH_TOKEN = "test-health-token-7c1d"  # noqa: S105 - test-only value


@pytest.fixture(autouse=True)
def health_token(settings):
    settings.HEALTH_CHECK_PASSWORD = HEALTH_TOKEN
    return HEALTH_TOKEN
