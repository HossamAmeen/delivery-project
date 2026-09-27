"""Assertions for the standard response envelope (api-contracts.md §1.2, DRF_SKILL §19).

All failure messages go through :func:`harness.secrets.redact`. Use these helpers instead of
bare ``assert`` whenever the compared value could contain a secret.
"""

from __future__ import annotations

import json
from typing import Any

import httpx

from harness.secrets import redact

# Strings that must never appear in an error body in production (DEBUG=False, generic 500).
LEAK_MARKERS = (
    "Traceback (most recent call last)",
    'File "/',
    "/srv/flash",
    "site-packages",
    "DEBUG = True",
    "You're seeing this error because you have",
    "django.core.exceptions",
)

GENERIC_MESSAGES = {
    "INVALID_CREDENTIALS": "Invalid username or password.",
    "TOKEN_INVALID": "Token is invalid or expired.",
    "NOT_AUTHENTICATED": "Authentication credentials were not provided.",
    "THROTTLED": "Request rate limit exceeded.",
}


def fail(msg: str) -> None:
    __tracebackhide__ = True
    raise AssertionError(redact(msg))


def check(condition: bool, msg: str) -> None:
    """``assert`` replacement whose message is always redacted."""
    __tracebackhide__ = True
    if not condition:
        fail(msg)


def describe(resp: httpx.Response, limit: int = 600) -> str:
    """A short, redacted description of a response for failure messages."""
    body = resp.text[:limit] if resp.content else "<empty body>"
    return redact(f"{resp.request.method} {resp.request.url.path} -> {resp.status_code}; body={body!r}")


def json_body(resp: httpx.Response) -> dict[str, Any]:
    __tracebackhide__ = True
    ctype = resp.headers.get("content-type", "")
    check("application/json" in ctype, f"expected a JSON response, got content-type {ctype!r}: {describe(resp)}")
    try:
        body = resp.json()
    except json.JSONDecodeError:
        fail(f"response is not valid JSON: {describe(resp)}")
    check(isinstance(body, dict), f"envelope must be a JSON object: {describe(resp)}")
    return body


def assert_no_leak(resp: httpx.Response) -> None:
    __tracebackhide__ = True
    text = resp.text
    for marker in LEAK_MARKERS:
        check(marker not in text, f"response leaks internals ({marker!r}): {describe(resp)}")


def assert_success(resp: httpx.Response, status: int = 200) -> Any:
    """Assert a success envelope and return its ``data``."""
    __tracebackhide__ = True
    check(resp.status_code == status, f"expected HTTP {status}: {describe(resp)}")
    body = json_body(resp)
    check(body.get("success") is True, f"'success' must be true: {describe(resp)}")
    check(isinstance(body.get("message"), str) and body["message"] != "", f"'message' must be a non-empty string: {describe(resp)}")
    check("data" in body, f"'data' key missing: {describe(resp)}")
    check("errors" not in body, f"success envelope must not carry 'errors': {describe(resp)}")
    return body["data"]


def assert_error(
    resp: httpx.Response,
    status: int,
    code: str | None = None,
    *,
    message: str | None = None,
    fields: tuple[str, ...] = (),
    require_code: bool | None = None,
) -> dict[str, Any]:
    """Assert an error envelope and return the whole body.

    ``code``: expected ``errors.code``. ``require_code`` defaults to True for every status
    except a 400 carrying field errors (api-contracts.md §1.2).
    ``fields``: field names that must appear under ``errors``.
    ``message``: exact expected message; defaults to the contract message of ``code`` if known.
    """
    __tracebackhide__ = True
    check(resp.status_code == status, f"expected HTTP {status}: {describe(resp)}")
    body = json_body(resp)
    check(body.get("success") is False, f"'success' must be false: {describe(resp)}")
    check(isinstance(body.get("message"), str) and body["message"] != "", f"'message' must be a non-empty string: {describe(resp)}")
    errors = body.get("errors")
    check(isinstance(errors, dict), f"'errors' must be an object: {describe(resp)}")
    check("data" not in body or body.get("data") is None, f"error envelope must not carry 'data': {describe(resp)}")
    for field in fields:
        check(field in errors, f"expected field error {field!r} under 'errors': {describe(resp)}")
        check(isinstance(errors[field], list) and errors[field], f"errors.{field} must be a non-empty list: {describe(resp)}")
    if require_code is None:
        require_code = not (status == 400 and fields)
    if code is not None:
        check(errors.get("code") == code, f"expected errors.code={code!r}, got {errors.get('code')!r}: {describe(resp)}")
    elif require_code:
        check(isinstance(errors.get("code"), str) and errors["code"], f"non-field error must carry errors.code: {describe(resp)}")
    expected_msg = message if message is not None else GENERIC_MESSAGES.get(code or "")
    if expected_msg is not None:
        check(body["message"] == expected_msg, f"expected message {expected_msg!r}, got {body['message']!r}: {describe(resp)}")
    assert_no_leak(resp)
    return body


def assert_throttled(resp: httpx.Response) -> None:
    """429 in the standard envelope, code THROTTLED, Retry-After kept (api-contracts § Error codes)."""
    __tracebackhide__ = True
    assert_error(resp, 429, "THROTTLED")
    retry_after = resp.headers.get("retry-after")
    check(retry_after is not None, f"429 must keep the Retry-After header: {describe(resp)}")
    check(retry_after.isdigit() and int(retry_after) > 0, f"Retry-After must be a positive integer, got {retry_after!r}")


def assert_not_in_response(resp: httpx.Response, secret: str, label: str) -> None:
    """The secret appears in neither the body nor any header value (message never shows it)."""
    __tracebackhide__ = True
    check(secret not in resp.text, f"{label} appears in the response body of {resp.request.url.path}")
    for name, value in resp.headers.items():
        check(secret not in value, f"{label} appears in response header {name!r} of {resp.request.url.path}")
