"""Application exceptions rendered by ``common.exception_handler``.

Raise these from services and views for business-rule failures. Each carries a
stable ``code`` (api-contracts.md § Error codes): clients branch on ``code``,
never on ``message``.
"""

from __future__ import annotations

from typing import Any


class ApplicationError(Exception):
    """Base class. Subclasses set ``status_code``, ``code`` and ``message``."""

    status_code: int = 400
    code: str = "APPLICATION_ERROR"
    message: str = "The request could not be processed."

    def __init__(
        self,
        message: str | None = None,
        *,
        code: str | None = None,
        status_code: int | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        if message is not None:
            self.message = message
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code
        # Additional keys rendered next to ``code`` inside ``errors``.
        self.extra = dict(extra or {})
        super().__init__(self.message)


class BusinessConflictError(ApplicationError):
    """The request conflicts with the current state (for example an invalid transition)."""

    status_code = 409
    code = "CONFLICT"
    message = "The request conflicts with the current state."


class BusinessValidationError(ApplicationError):
    """A business rule rejected otherwise well-formed input."""

    status_code = 400
    code = "VALIDATION_ERROR"
    message = "Validation failed."
