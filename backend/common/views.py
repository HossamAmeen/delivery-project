"""Envelope responses for URLs that never reach a DRF view (Django handler404/500)."""

from __future__ import annotations

from django.http import JsonResponse

from .exception_handler import SERVER_ERROR_MESSAGE
from .responses import error_body


def page_not_found(request, exception=None) -> JsonResponse:
    return JsonResponse(error_body("Not found.", {"code": "NOT_FOUND"}), status=404)


def server_error(request) -> JsonResponse:
    return JsonResponse(error_body(SERVER_ERROR_MESSAGE, {"code": "SERVER_ERROR"}), status=500)
