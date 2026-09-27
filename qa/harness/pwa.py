"""Shared constants and mock bodies for the Playwright tests (qa/e2e/)."""

from __future__ import annotations

import json
import re

MOBILE = {"width": 360, "height": 780}
DESKTOP = {"width": 1280, "height": 800}
VIEWPORTS = {"mobile-360": MOBILE, "desktop-1280": DESKTOP}

# Selectors confirmed 2026-09-28 against the built PWA (frontend/src/i18n/en.ts, views and
# state components of TASK-007). QA adjusts selectors here — never the expected behaviour.
USERNAME_LABEL = re.compile(r"user\s*name", re.I)
PASSWORD_LABEL = re.compile(r"password", re.I)
LOGIN_BUTTON = re.compile(r"^\s*(log\s*in|sign\s*in)\s*$", re.I)
LOGOUT_BUTTON = re.compile(r"(log\s*out|sign\s*out)", re.I)
RETRY_BUTTON = re.compile(r"(retry|try again)", re.I)
API_REACHABLE = re.compile(r"API reachable", re.I)
API_UNREACHABLE = re.compile(r"(unreachable|unavailable)", re.I)
RATE_LIMITED = re.compile(r"(rate.?limit|too many)", re.I)
LOADING = re.compile(r"(loading|checking)", re.I)
# data-testid hooks present in the build (state components, status page, logout button).
TID_LOADING = "state-loading"
TID_ERROR = "state-error"
TID_UNAVAILABLE = "state-unavailable"
TID_EMPTY = "state-empty"
TID_STATUS_OK = "status-ok"
TID_SESSION_USER = "session-user"
TID_FORM_ERROR = "form-error"
NOT_FOUND = re.compile(r"(not found|404)", re.I)

# Fake JWT-shaped strings for fully mocked flows (never valid on the server).
FAKE_ACCESS = "eyJhbGciOiJIUzI1NiJ9.eyJxYSI6ImFjY2VzcyJ9.cWEtZmFrZS1hY2Nlc3M"
FAKE_ACCESS_2 = "eyJhbGciOiJIUzI1NiJ9.eyJxYSI6ImFjY2VzczIifQ.cWEtZmFrZS1hY2Nlc3My"
FAKE_REFRESH = "eyJhbGciOiJIUzI1NiJ9.eyJxYSI6InJlZnJlc2gifQ.cWEtZmFrZS1yZWZyZXNo"


# Mocked cross-origin responses need CORS headers or the browser discards them. The PWA uses
# no credentials mode (TASK-007), so a wildcard origin is valid for mocks.
MOCK_CORS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "*",
    "Access-Control-Expose-Headers": "Retry-After",
}


def envelope_ok(data: dict, status: int = 200, headers: dict | None = None) -> dict:
    return {
        "status": status,
        "content_type": "application/json",
        "headers": {**MOCK_CORS, **(headers or {})},
        "body": json.dumps({"success": True, "message": "Operation completed successfully.", "data": data}),
    }


def envelope_error(status: int, code: str, message: str, headers: dict | None = None) -> dict:
    return {
        "status": status,
        "content_type": "application/json",
        "headers": {**MOCK_CORS, **(headers or {})},
        "body": json.dumps({"success": False, "message": message, "errors": {"code": code}}),
    }


def no_horizontal_overflow(page) -> bool:
    return page.evaluate("() => document.documentElement.scrollWidth <= window.innerWidth + 1")
