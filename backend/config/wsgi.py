"""WSGI entry point (gunicorn: ``config.wsgi:application``).

Defaults to production settings; ``DJANGO_SETTINGS_MODULE`` from the environment wins.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

application = get_wsgi_application()
