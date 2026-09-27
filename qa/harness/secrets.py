"""Secret handling for the QA harness.

Rules (ADR-015, ADR-018, TASK-008):
- The health token, QA passwords and every JWT the suite obtains are registered here.
- Anything that can end up in an assertion message, a log line, the JUnit XML or the
  terminal goes through :func:`redact` first. `conftest.py` also scrubs every test report.
- Secrets are wrapped in :class:`Secret`, whose ``repr``/``str`` never show the value, so a
  failing assertion that introspects a local variable cannot leak it.
"""

from __future__ import annotations

import re
import threading

REDACTED = "[REDACTED]"

_JWT_RE = re.compile(r"eyJ[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]*")
_QUERY_SECRET_RE = re.compile(r"(?i)((?:password|token|secret)=)[^&\s\"']+")
_AUTH_HEADER_RE = re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._-]+")

_lock = threading.Lock()
_registered: set[str] = set()


class Secret:
    """A secret value that never prints itself."""

    __slots__ = ("_value",)

    def __init__(self, value: str) -> None:
        self._value = value
        register(value)

    def reveal(self) -> str:
        return self._value

    def __bool__(self) -> bool:
        return bool(self._value)

    def __repr__(self) -> str:
        return "Secret([REDACTED])"

    __str__ = __repr__


def register(value: str | None) -> None:
    """Register a value that must never appear in output (min. 4 chars)."""
    if value and len(value) >= 4:
        with _lock:
            _registered.add(value)


def registered_values() -> list[str]:
    with _lock:
        return sorted(_registered, key=len, reverse=True)


def redact(text: object) -> str:
    """Return ``text`` as a string with every known secret and JWT removed."""
    out = text if isinstance(text, str) else str(text)
    for value in registered_values():
        if value in out:
            out = out.replace(value, REDACTED)
    out = _JWT_RE.sub("[REDACTED-JWT]", out)
    out = _QUERY_SECRET_RE.sub(r"\1" + REDACTED, out)
    out = _AUTH_HEADER_RE.sub(r"\1" + REDACTED, out)
    return out


def count_secret_occurrences(text: str) -> int:
    """How many times any registered secret appears in ``text`` (for count-only scans)."""
    return sum(text.count(v) for v in registered_values())
