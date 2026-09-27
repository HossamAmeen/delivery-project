"""OpenAPI support (DRF_SKILL §21, §76; ADR-019).

- ``envelope_postprocessing_hook`` documents the standard success envelope on
  every 2xx JSON response and a 429 error response on every operation.
- ``ErrorEnvelopeSerializer`` documents error responses in views.
- ``SchemaView`` / ``SwaggerView`` / ``RedocView`` serve the docs: public when
  ``API_DOCS_PUBLIC`` is true, otherwise staff only (JWT bearer or admin session).
  Their error responses are rendered as the JSON error envelope.
"""

from __future__ import annotations

from typing import Any

from django.conf import settings
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework import serializers
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import BasePermission
from rest_framework_simplejwt.authentication import JWTAuthentication

from .renderers import EnvelopeJSONRenderer

ERROR_ENVELOPE_REF = "#/components/schemas/ErrorEnvelope"
TOO_MANY_REQUESTS_REF = "#/components/responses/TooManyRequests"


class ErrorEnvelopeSerializer(serializers.Serializer):
    """``{"success": false, "message": "...", "errors": {"code": "..."}}``"""

    success = serializers.BooleanField(default=False)
    message = serializers.CharField()
    errors = serializers.DictField(help_text="Field errors, or `code` plus details.")


def _wrap_success(schema: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "object",
        "required": ["success", "message", "data"],
        "properties": {
            "success": {"type": "boolean", "example": True},
            "message": {"type": "string", "example": "Operation completed successfully."},
            "data": schema,
        },
    }


def envelope_postprocessing_hook(result, generator, request, public):  # noqa: ARG001
    components = result.setdefault("components", {})
    components.setdefault("schemas", {}).setdefault(
        "ErrorEnvelope",
        {
            "type": "object",
            "required": ["success", "message", "errors"],
            "properties": {
                "success": {"type": "boolean", "example": False},
                "message": {"type": "string"},
                "errors": {"type": "object", "additionalProperties": {}},
            },
        },
    )
    components.setdefault("responses", {})["TooManyRequests"] = {
        "description": "Rate limit exceeded (`errors.code` = `THROTTLED`). "
        "The `Retry-After` header gives the wait in seconds.",
        "headers": {"Retry-After": {"schema": {"type": "integer"}}},
        "content": {"application/json": {"schema": {"$ref": ERROR_ENVELOPE_REF}}},
    }

    for path_item in result.get("paths", {}).values():
        for operation in path_item.values():
            if not isinstance(operation, dict) or "responses" not in operation:
                continue
            responses = operation["responses"]
            for status_code, response in responses.items():
                if not str(status_code).startswith("2") or str(status_code) == "204":
                    continue
                content = response.get("content", {}).get("application/json")
                if content and "schema" in content:
                    content["schema"] = _wrap_success(content["schema"])
            responses.setdefault("429", {"$ref": TOO_MANY_REQUESTS_REF})
    return result


class DocsAccessPermission(BasePermission):
    """ADR-019: docs are public only when ``API_DOCS_PUBLIC`` is true."""

    message = "Staff access is required for the API documentation."

    def has_permission(self, request, view) -> bool:
        if getattr(settings, "API_DOCS_PUBLIC", False):
            return True
        user = request.user
        return bool(user and user.is_authenticated and user.is_staff)


class EnvelopeErrorsMixin:
    """Render error responses of non-JSON views (YAML, HTML) as the JSON error envelope."""

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        if response.status_code >= 400:
            response.accepted_renderer = EnvelopeJSONRenderer()
            response.accepted_media_type = EnvelopeJSONRenderer.media_type
            response.renderer_context = self.get_renderer_context()
        return response


DOCS_AUTHENTICATION = [JWTAuthentication, SessionAuthentication]


class SchemaView(EnvelopeErrorsMixin, SpectacularAPIView):
    authentication_classes = DOCS_AUTHENTICATION
    permission_classes = [DocsAccessPermission]


class SwaggerView(EnvelopeErrorsMixin, SpectacularSwaggerView):
    authentication_classes = DOCS_AUTHENTICATION
    permission_classes = [DocsAccessPermission]


class RedocView(EnvelopeErrorsMixin, SpectacularRedocView):
    authentication_classes = DOCS_AUTHENTICATION
    permission_classes = [DocsAccessPermission]
