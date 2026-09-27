"""Celery application (DRF_SKILL §29). Optional: CELERY_ENABLED toggles it.

Importing this module never connects to a broker. With CELERY_ENABLED=False
(the server, ADR-017) the settings make every task run inline.
"""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

app = Celery("flash")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
