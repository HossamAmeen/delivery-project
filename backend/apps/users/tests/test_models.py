"""User model and manager (ADR-003)."""

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction

pytestmark = pytest.mark.django_db

User = get_user_model()


def test_auth_user_model_is_the_custom_user():
    assert User._meta.label == "users.User"
    assert User.USERNAME_FIELD == "username"
    assert User.Role.values == ["CUSTOMER", "DRIVER", "STORE", "ADMIN"]


@pytest.mark.parametrize("role", ["CUSTOMER", "DRIVER", "STORE", "ADMIN"])
def test_create_user_with_each_role(role):
    user = User.objects.create_user(username=f"u_{role.lower()}", password="x-Pass-123!", role=role)

    assert user.role == role
    assert user.is_staff is False
    assert user.is_superuser is False
    assert user.check_password("x-Pass-123!")
    assert str(user) == f"u_{role.lower()}"


def test_create_user_requires_role():
    with pytest.raises(ValueError, match="role is required"):
        User.objects.create_user(username="norole", password="x-Pass-123!")


def test_create_user_rejects_unknown_role():
    with pytest.raises(ValueError):
        User.objects.create_user(username="bad", password="x-Pass-123!", role="SUPERHERO")


def test_create_superuser_gets_admin_role_and_staff():
    admin = User.objects.create_superuser(username="root", password="x-Pass-123!")

    assert admin.role == User.Role.ADMIN
    assert admin.is_staff is True
    assert admin.is_superuser is True


def test_create_superuser_rejects_other_roles():
    with pytest.raises(ValueError, match="ADMIN"):
        User.objects.create_superuser(username="root", password="x-Pass-123!", role="DRIVER")


@pytest.mark.parametrize("flag", ["is_staff", "is_superuser"])
def test_create_superuser_rejects_false_flags(flag):
    with pytest.raises(ValueError):
        User.objects.create_superuser(username="root", password="x-Pass-123!", **{flag: False})


def test_username_is_unique_across_roles(make_user):
    make_user("sam", role=User.Role.CUSTOMER)

    with pytest.raises(IntegrityError), transaction.atomic():
        User.objects.create_user(username="sam", password="x-Pass-123!", role=User.Role.DRIVER)


def test_username_is_case_sensitive(make_user):
    make_user("Sam")
    other = make_user("sam")

    assert other.pk is not None


def test_username_is_unicode_normalized():
    # "ﬁ" (U+FB01 ligature) NFKC-normalizes to "fi" (Django's AbstractUser behaviour).
    user = User.objects.create_user(username="ﬁsh", password="x-Pass-123!", role="CUSTOMER")

    assert user.username == "fish"


def test_database_rejects_an_invalid_role(make_user):
    user = make_user("eve")

    with pytest.raises(IntegrityError), transaction.atomic():
        User.objects.filter(pk=user.pk).update(role="HACKER")
