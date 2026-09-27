"""Default renderer that applies the standard success envelope (DRF_SKILL §19).

Pre-approved mechanism (TASK-002): any response whose data is not already an
envelope is wrapped as ``{"success": true, "message": ..., "data": ...}``.
Errors are enveloped by the exception handler and pass through untouched.
A 204 response has no body. drf-spectacular views use their own renderers.
"""

from __future__ import annotations

from typing import Any

from rest_framework.renderers import JSONRenderer

from .responses import DEFAULT_SUCCESS_MESSAGE, error_body, is_envelope

DEFAULT_ERROR_MESSAGE = "Request failed."


class EnvelopeJSONRenderer(JSONRenderer):
    def render(
        self,
        data: Any,
        accepted_media_type: str | None = None,
        renderer_context: dict[str, Any] | None = None,
    ) -> bytes:
        response = (renderer_context or {}).get("response")
        if response is None:
            return super().render(data, accepted_media_type, renderer_context)
        if response.status_code == 204:
            return b""
        if not is_envelope(data):
            data = self._wrap(data, response)
        return super().render(data, accepted_media_type, renderer_context)

    @staticmethod
    def _wrap(data: Any, response: Any) -> dict[str, Any]:
        message = getattr(response, "message", None)
        if response.status_code >= 400:
            # A view returned an error payload directly instead of raising.
            errors = data if isinstance(data, dict) else {"detail": data}
            return error_body(message or DEFAULT_ERROR_MESSAGE, errors)
        return {"success": True, "message": message or DEFAULT_SUCCESS_MESSAGE, "data": data}
