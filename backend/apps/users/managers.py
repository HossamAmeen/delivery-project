"""User manager: ``role`` is required, superusers are always ADMIN."""

from __future__ import annotations

from django.contrib.auth.models import UserManager as DjangoUserManager


class UserManager(DjangoUserManager):
    use_in_migrations = True

    def _validate_role(self, role):
        valid = self.model.Role.values
        if role not in valid:
            raise ValueError(f"role is required and must be one of {', '.join(valid)}.")
        return role

    def create_user(self, username, email=None, password=None, role=None, **extra_fields):
        extra_fields["role"] = self._validate_role(role)
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(username, email, password, **extra_fields)

    def create_superuser(self, username, email=None, password=None, role=None, **extra_fields):
        admin = self.model.Role.ADMIN
        if role not in (None, admin):
            raise ValueError("A superuser must have the ADMIN role.")
        extra_fields["role"] = admin
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(username, email, password, **extra_fields)
