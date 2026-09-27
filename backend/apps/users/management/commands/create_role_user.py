"""Create or update a user with a role (used by ``make seed-qa-users``, ADR-018).

The password is read from stdin (``--password-stdin``, first line) or from the
``FLASH_NEW_USER_PASSWORD`` environment variable. It is never accepted on the
command line and never printed.
"""

from __future__ import annotations

import os
import sys

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

PASSWORD_ENV_VAR = "FLASH_NEW_USER_PASSWORD"  # noqa: S105 - variable name, not a secret


class Command(BaseCommand):
    help = (
        "Create a user with a role, or update it with --update (sets password, role, "
        "is_staff and is_superuser to the given values). Password from --password-stdin "
        f"or ${PASSWORD_ENV_VAR}; never from argv."
    )
    # Lets tests pass a stdin stream through call_command().
    stealth_options = ("stdin",)

    def add_arguments(self, parser):
        user_model = get_user_model()
        parser.add_argument("--username", required=True)
        parser.add_argument("--role", required=True, choices=user_model.Role.values)
        parser.add_argument("--staff", action="store_true", help="Grant admin-site access.")
        parser.add_argument(
            "--superuser", action="store_true", help="Superuser (requires --role ADMIN)."
        )
        parser.add_argument("--update", action="store_true", help="Update an existing user.")
        parser.add_argument(
            "--password-stdin", action="store_true", help="Read the password from stdin."
        )

    def handle(self, *args, **options):
        user_model = get_user_model()
        username = options["username"]
        role = options["role"]
        superuser = options["superuser"]
        staff = options["staff"] or superuser

        if superuser and role != user_model.Role.ADMIN:
            raise CommandError("--superuser requires --role ADMIN.")

        password = self._read_password(options)

        with transaction.atomic():
            user = user_model.objects.filter(username=username).select_for_update().first()
            if user is not None and not options["update"]:
                raise CommandError(f"User '{username}' already exists; use --update to change it.")
            if user is None:
                user = user_model(username=username)
                created = True
            else:
                created = False
            user.role = role
            user.is_staff = staff
            user.is_superuser = superuser
            self._validate_password(password, user)
            user.set_password(password)
            user.save()

        action = "Created" if created else "Updated"
        flags = [name for name, on in (("staff", staff), ("superuser", superuser)) if on]
        suffix = f" ({', '.join(flags)})" if flags else ""
        self.stdout.write(
            self.style.SUCCESS(f"{action} user '{username}' with role {role}{suffix}.")
        )

    def _read_password(self, options) -> str:
        if options["password_stdin"]:
            stream = options.get("stdin") or sys.stdin
            password = stream.readline().rstrip("\r\n")
            source = "stdin"
        else:
            password = os.environ.get(PASSWORD_ENV_VAR, "")
            source = PASSWORD_ENV_VAR
        if not password:
            raise CommandError(
                f"No password given: use --password-stdin or set {PASSWORD_ENV_VAR} "
                f"(read from {source})."
            )
        return password

    @staticmethod
    def _validate_password(password: str, user) -> None:
        try:
            validate_password(password, user)
        except ValidationError as exc:
            # Validator messages describe the rule, never the password itself.
            raise CommandError("Password rejected: " + " ".join(exc.messages)) from exc
