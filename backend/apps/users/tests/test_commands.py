"""create_role_user management command (ADR-018 seeding)."""

import io

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError

pytestmark = pytest.mark.django_db

User = get_user_model()
PASSWORD = "Seed-Pa55word-4-QA!"  # noqa: S105 - test-only value
OTHER_PASSWORD = "Another-Pa55word-4-QA!"  # noqa: S105


def run(*args, stdin=None):
    out, err = io.StringIO(), io.StringIO()
    kwargs = {"stdout": out, "stderr": err}
    if stdin is not None:
        kwargs["stdin"] = io.StringIO(stdin)
    call_command("create_role_user", *args, **kwargs)
    return out.getvalue() + err.getvalue()


def test_creates_user_with_password_from_env(monkeypatch):
    monkeypatch.setenv("FLASH_NEW_USER_PASSWORD", PASSWORD)

    output = run("--username", "qa_driver", "--role", "DRIVER")

    user = User.objects.get(username="qa_driver")
    assert user.role == "DRIVER"
    assert user.check_password(PASSWORD)
    assert user.is_staff is False
    assert "Created user 'qa_driver' with role DRIVER." in output
    assert PASSWORD not in output


def test_creates_superuser_with_password_from_stdin(monkeypatch):
    monkeypatch.delenv("FLASH_NEW_USER_PASSWORD", raising=False)

    output = run(
        "--username",
        "qa_admin",
        "--role",
        "ADMIN",
        "--superuser",
        "--password-stdin",
        stdin=PASSWORD + "\n",
    )

    user = User.objects.get(username="qa_admin")
    assert user.check_password(PASSWORD)
    assert (user.role, user.is_staff, user.is_superuser) == ("ADMIN", True, True)
    assert PASSWORD not in output


def test_staff_flag(monkeypatch):
    monkeypatch.setenv("FLASH_NEW_USER_PASSWORD", PASSWORD)

    run("--username", "qa_store", "--role", "STORE", "--staff")

    user = User.objects.get(username="qa_store")
    assert (user.is_staff, user.is_superuser) == (True, False)


def test_existing_user_without_update_is_an_error(monkeypatch, make_user):
    make_user("qa_customer")
    monkeypatch.setenv("FLASH_NEW_USER_PASSWORD", PASSWORD)

    with pytest.raises(CommandError, match="--update"):
        run("--username", "qa_customer", "--role", "CUSTOMER")


def test_update_sets_password_role_and_flags_idempotently(monkeypatch, make_user):
    make_user("qa_x", role="CUSTOMER", is_staff=True)
    monkeypatch.setenv("FLASH_NEW_USER_PASSWORD", OTHER_PASSWORD)

    for _ in range(2):
        output = run("--username", "qa_x", "--role", "DRIVER", "--update")

    user = User.objects.get(username="qa_x")
    assert user.check_password(OTHER_PASSWORD)
    assert (user.role, user.is_staff, user.is_superuser) == ("DRIVER", False, False)
    assert User.objects.filter(username="qa_x").count() == 1
    assert "Updated user 'qa_x' with role DRIVER." in output


def test_update_creates_a_missing_user(monkeypatch):
    monkeypatch.setenv("FLASH_NEW_USER_PASSWORD", PASSWORD)

    output = run("--username", "qa_new", "--role", "CUSTOMER", "--update")

    assert User.objects.filter(username="qa_new").exists()
    assert "Created" in output


def test_superuser_requires_admin_role(monkeypatch):
    monkeypatch.setenv("FLASH_NEW_USER_PASSWORD", PASSWORD)

    with pytest.raises(CommandError, match="--role ADMIN"):
        run("--username", "bad", "--role", "DRIVER", "--superuser")
    assert not User.objects.filter(username="bad").exists()


def test_missing_password_is_an_error(monkeypatch):
    monkeypatch.delenv("FLASH_NEW_USER_PASSWORD", raising=False)

    with pytest.raises(CommandError, match="No password given"):
        run("--username", "nopass", "--role", "CUSTOMER")


def test_empty_stdin_is_an_error(monkeypatch):
    monkeypatch.setenv("FLASH_NEW_USER_PASSWORD", PASSWORD)

    with pytest.raises(CommandError, match="No password given"):
        run("--username", "nopass", "--role", "CUSTOMER", "--password-stdin", stdin="")


def test_weak_password_is_rejected_without_echoing_it(monkeypatch):
    monkeypatch.setenv("FLASH_NEW_USER_PASSWORD", "123")

    with pytest.raises(CommandError) as excinfo:
        run("--username", "weak", "--role", "CUSTOMER")

    assert "Password rejected" in str(excinfo.value)
    assert "'123'" not in str(excinfo.value)
    assert not User.objects.filter(username="weak").exists()


def test_invalid_role_is_rejected(monkeypatch):
    monkeypatch.setenv("FLASH_NEW_USER_PASSWORD", PASSWORD)

    with pytest.raises(CommandError):
        run("--username", "x", "--role", "HACKER")


def test_password_is_never_accepted_on_the_command_line():
    with pytest.raises(CommandError):
        run("--username", "x", "--role", "CUSTOMER", "--password", PASSWORD)
    assert not User.objects.filter(username="x").exists()
