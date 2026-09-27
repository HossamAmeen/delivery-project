"""Custom user with a role, from the first migration (ADR-003)."""

from django.contrib.auth.models import AbstractUser
from django.db import models

from .managers import UserManager


class User(AbstractUser):
    class Role(models.TextChoices):
        CUSTOMER = "CUSTOMER", "Customer"
        DRIVER = "DRIVER", "Driver"
        STORE = "STORE", "Store"
        ADMIN = "ADMIN", "Admin"

    # Required, no default (TASK-003). Read-only through every API.
    role = models.CharField(max_length=16, choices=Role.choices, db_index=True)

    objects = UserManager()

    # Login is username + password (BLK-001); Django defaults kept explicit.
    USERNAME_FIELD = "username"

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(role__in=["CUSTOMER", "DRIVER", "STORE", "ADMIN"]),
                name="users_user_role_valid",
            ),
        ]

    def __str__(self) -> str:
        return self.username
