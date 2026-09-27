"""Concrete model to exercise the abstract BaseModel (no migrations: created by syncdb)."""

from django.db import models

from common.models import BaseModel


class Widget(BaseModel):
    name = models.CharField(max_length=50)

    class Meta:
        app_label = "testapp"
        ordering = ["id"]

    def __str__(self) -> str:
        return self.name
