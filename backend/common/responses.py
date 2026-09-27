"""Standard success responses (DRF_SKILL §19).

Views normally return a plain ``Response``; ``EnvelopeJSONRenderer`` wraps it.
Use ``success_response`` when a view needs a specific message.
"""

from __future__ import annotations

from typing import Any

from rest_framework import status as http_status
from rest_framework.response import Response

DEFAULT_SUCCESS_MESSAGE = "Operation completed successfully."


def is_envelope(data: Any) -> bool:
    """True when ``data`` already has the standard envelope shape."""
    return (
        isinstance(data, dict)
        and isinstance(data.get("success"), bool)
        and "message" in data
        and ("data" in data or "errors" in data)
    )


def success_response(
    data: Any = None,
    message: str = DEFAULT_SUCCESS_MESSAGE,
    status: int = http_status.HTTP_200_OK,
    headers: dict[str, str] | None = None,
) -> Response:
    response = Response(data, status=status, headers=headers)
    response.message = message
    return response


def error_body(message: str, errors: dict[str, Any]) -> dict[str, Any]:
    return {"success": False, "message": message, "errors": errors}
