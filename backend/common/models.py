"""Abstract base model with timestamps and soft delete (DRF_SKILL §11-13)."""

from django.db import models
from django.utils import timezone

from .managers import ActiveManager, AllManager, DeletedManager


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    # The first manager is the default one: active rows only. Related-object
    # access uses Django's plain base manager, so relations still resolve.
    objects = ActiveManager()
    deleted_objects = DeletedManager()
    all_objects = AllManager()

    class Meta:
        abstract = True

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        """Mark the row as deleted instead of removing it."""
        if self.deleted_at is None:
            self.deleted_at = timezone.now()
            self.save(update_fields=["deleted_at", "modified_at"])

    def restore(self) -> None:
        """Undo a soft delete."""
        if self.deleted_at is not None:
            self.deleted_at = None
            self.save(update_fields=["deleted_at", "modified_at"])
