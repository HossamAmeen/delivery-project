"""Root URL configuration (paths per DRF_SKILL, no version prefix: ADR-010)."""

from django.contrib import admin
from django.urls import include, path

from apps.users.urls import auth_urlpatterns, users_urlpatterns
from common.openapi import RedocView, SchemaView, SwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    # Health / status (TASK-004)
    path("api/", include("apps.health.urls")),
    # Identity (TASK-003)
    path("api/auth/", include(auth_urlpatterns)),
    path("api/users/", include(users_urlpatterns)),
    # OpenAPI (TASK-004; staff-only in production, ADR-019)
    path("api/schema/", SchemaView.as_view(), name="schema"),
    path("api/docs/", SwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", RedocView.as_view(url_name="schema"), name="redoc"),
]

# JSON envelope for URLs that never reach a DRF view.
handler404 = "common.views.page_not_found"
handler500 = "common.views.server_error"
