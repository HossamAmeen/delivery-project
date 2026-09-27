"""Role permission classes (authorization step 2 of business-logic §3)."""

from rest_framework.permissions import BasePermission

from .models import User


class HasRole(BasePermission):
    role: str | None = None
    message = "You do not have permission to perform this action."

    def has_permission(self, request, view) -> bool:
        user = request.user
        return bool(user and user.is_authenticated and user.is_active and user.role == self.role)


class IsCustomer(HasRole):
    role = User.Role.CUSTOMER


class IsDriver(HasRole):
    role = User.Role.DRIVER


class IsStoreUser(HasRole):
    role = User.Role.STORE


class IsPlatformAdmin(HasRole):
    role = User.Role.ADMIN
