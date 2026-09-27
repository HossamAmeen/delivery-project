"""Django admin (Jazzmin): staff only."""

import pytest

pytestmark = pytest.mark.django_db

CHANGELIST = "/admin/users/user/"


def test_anonymous_is_redirected_to_admin_login(client):
    response = client.get(CHANGELIST)

    assert response.status_code == 302
    assert "/admin/login/" in response["Location"]


def test_non_staff_user_is_redirected_to_admin_login(client, make_user):
    client.force_login(make_user("customer"))

    response = client.get(CHANGELIST)

    assert response.status_code == 302
    assert "/admin/login/" in response["Location"]


def test_superuser_sees_the_user_changelist_with_role_filter(client, django_user_model):
    admin = django_user_model.objects.create_superuser(username="root", password="x-Pass-123!")
    client.force_login(admin)

    response = client.get(CHANGELIST, {"role__exact": "ADMIN", "q": "root"})

    assert response.status_code == 200
    assert b"root" in response.content


def test_superuser_can_open_the_add_form_with_role(client, django_user_model):
    admin = django_user_model.objects.create_superuser(username="root", password="x-Pass-123!")
    client.force_login(admin)

    response = client.get(f"{CHANGELIST}add/")

    assert response.status_code == 200
    assert b'name="role"' in response.content


def test_admin_uses_jazzmin_branding(client, django_user_model):
    admin = django_user_model.objects.create_superuser(username="root", password="x-Pass-123!")
    client.force_login(admin)

    response = client.get("/admin/")

    assert response.status_code == 200
    assert b"Flash" in response.content
