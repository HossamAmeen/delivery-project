"""Role permission classes: allow + deny per role."""

import pytest
from django.contrib.auth.models import AnonymousUser
from rest_framework.test import APIRequestFactory

from apps.users.permissions import IsCustomer, IsDriver, IsPlatformAdmin, IsStoreUser

pytestmark = pytest.mark.django_db

CASES = [
    (IsCustomer, "CUSTOMER"),
    (IsDriver, "DRIVER"),
    (IsStoreUser, "STORE"),
    (IsPlatformAdmin, "ADMIN"),
]
ROLES = ["CUSTOMER", "DRIVER", "STORE", "ADMIN"]


def request_for(user):
    request = APIRequestFactory().get("/")
    request.user = user
    return request


@pytest.mark.parametrize(("permission_class", "role"), CASES)
def test_permission_allows_its_role(make_user, permission_class, role):
    user = make_user(f"u_{role.lower()}", role=role)

    assert permission_class().has_permission(request_for(user), view=None) is True


@pytest.mark.parametrize(("permission_class", "role"), CASES)
def test_permission_denies_other_roles(make_user, permission_class, role):
    for other in (r for r in ROLES if r != role):
        user = make_user(f"u_{other.lower()}_{role.lower()}", role=other)
        assert permission_class().has_permission(request_for(user), view=None) is False


@pytest.mark.parametrize(("permission_class", "role"), CASES)
def test_permission_denies_anonymous(permission_class, role):
    assert permission_class().has_permission(request_for(AnonymousUser()), view=None) is False


@pytest.mark.parametrize(("permission_class", "role"), CASES)
def test_permission_denies_inactive_user(make_user, permission_class, role):
    user = make_user(f"inactive_{role.lower()}", role=role, is_active=False)

    assert permission_class().has_permission(request_for(user), view=None) is False


def test_staff_flag_alone_does_not_grant_platform_admin(make_user):
    staff_customer = make_user("staff_customer", role="CUSTOMER", is_staff=True)

    assert IsPlatformAdmin().has_permission(request_for(staff_customer), view=None) is False
