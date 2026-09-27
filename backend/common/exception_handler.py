"""Centralized DRF exception handling (DRF_SKILL §20).

Every error leaves the API as
``{"success": false, "message": "...", "errors": {...}}``. Errors that are not
field validation errors carry ``errors.code`` (api-contracts.md § Error codes).
"""

from __future__ import annotations

import logging
from typing import Any

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.serializers import as_serializer_error
from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.views import set_rollback

from .exceptions import ApplicationError
from .responses import error_body

logger = logging.getLogger("common.exceptions")

NON_FIELD_ERRORS_KEY = "non_field_errors"
SERVER_ERROR_MESSAGE = "An unexpected error occurred."
TOKEN_INVALID_MESSAGE = "Token is invalid or expired."  # noqa: S105 - message, not a secret

# (exception class, code, fixed message or None to use the exception detail).
# Order matters: the first matching class wins.
_ERROR_TABLE: tuple[tuple[type[exceptions.APIException], str, str | None], ...] = (
    (exceptions.NotAuthenticated, "NOT_AUTHENTICATED", None),
    # Every authentication failure on a protected endpoint is a bad/expired
    # token (simplejwt's InvalidToken subclasses AuthenticationFailed). Login
    # failures are raised as ApplicationError INVALID_CREDENTIALS instead.
    (exceptions.AuthenticationFailed, "TOKEN_INVALID", TOKEN_INVALID_MESSAGE),
    (exceptions.PermissionDenied, "PERMISSION_DENIED", None),
    (exceptions.NotFound, "NOT_FOUND", "Not found."),
    (exceptions.MethodNotAllowed, "METHOD_NOT_ALLOWED", None),
    (exceptions.NotAcceptable, "NOT_ACCEPTABLE", None),
    (exceptions.UnsupportedMediaType, "UNSUPPORTED_MEDIA_TYPE", None),
    (exceptions.ParseError, "PARSE_ERROR", None),
    (exceptions.Throttled, "THROTTLED", "Request rate limit exceeded."),
)


def custom_exception_handler(exc: Exception, context: dict[str, Any]) -> Response:
    if isinstance(exc, ApplicationError):
        set_rollback()
        return Response(
            error_body(exc.message, {"code": exc.code, **exc.extra}),
            status=exc.status_code,
        )

    exc = _convert_django_exception(exc)
    response = drf_exception_handler(exc, context)

    if response is None:
        # Not an APIException: log it server-side, answer generically.
        view = context.get("view")
        logger.exception(
            "Unhandled exception in %s", type(view).__name__ if view else "unknown view"
        )
        set_rollback()
        return Response(
            error_body(SERVER_ERROR_MESSAGE, {"code": "SERVER_ERROR"}),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    if isinstance(exc, exceptions.ValidationError):
        response.data = _validation_body(response.data)
    else:
        message, code = _describe(exc)
        response.data = error_body(message, {"code": code})
    # DRF's own headers (Retry-After, WWW-Authenticate, Allow) are kept.
    return response


def _convert_django_exception(exc: Exception) -> Exception:
    if isinstance(exc, Http404):
        return exceptions.NotFound()
    if isinstance(exc, DjangoPermissionDenied):
        return exceptions.PermissionDenied()
    if isinstance(exc, DjangoValidationError):
        return exceptions.ValidationError(as_serializer_error(exc))
    return exc


def _validation_body(detail: Any) -> dict[str, Any]:
    if isinstance(detail, dict):
        errors = dict(detail)
    else:
        errors = {NON_FIELD_ERRORS_KEY: detail if isinstance(detail, list) else [detail]}
    field_errors = [key for key in errors if key != NON_FIELD_ERRORS_KEY]
    if not field_errors:
        errors["code"] = "VALIDATION_ERROR"
    return error_body("Validation failed.", errors)


def _describe(exc: exceptions.APIException) -> tuple[str, str]:
    for exc_class, code, message in _ERROR_TABLE:
        if isinstance(exc, exc_class):
            return message or _detail_message(exc), code
    if exc.status_code >= 500:
        return SERVER_ERROR_MESSAGE, "SERVER_ERROR"
    return _detail_message(exc), str(exc.default_code).upper()


def _detail_message(exc: exceptions.APIException) -> str:
    detail = exc.detail
    if isinstance(detail, str):
        return str(detail)
    return str(exc.default_detail)
