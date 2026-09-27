"""Soft-delete aware managers (DRF_SKILL §13)."""

from django.db import models


class ActiveManager(models.Manager):
    """Rows that are not soft-deleted (the default manager)."""

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class DeletedManager(models.Manager):
    """Soft-deleted rows only."""

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=False)


class AllManager(models.Manager):
    """Every row, deleted or not."""

    def get_queryset(self):
        return super().get_queryset()
