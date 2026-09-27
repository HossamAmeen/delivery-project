"""HTTP clients, JWT helpers and the auth-endpoint pacer."""

from __future__ import annotations

import base64
import collections
import json
import logging
import re
import threading
import time
from typing import Any

import httpx

from harness.config import QAConfig, parse_rate
from harness.secrets import Secret, register

log = logging.getLogger("qa.http")

USER_AGENT = "flash-qa-harness/1.0 (+qa/README.md)"


def _log_response(resp: httpx.Response) -> None:
    # Evidence line: method, path (never the query string), status. Nothing else.
    log.info("%s %s%s -> %s", resp.request.method, resp.request.url.host, resp.request.url.path, resp.status_code)


def make_client(base_url: str, cfg: QAConfig, **kwargs: Any) -> httpx.Client:
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    headers.update(kwargs.pop("headers", {}))
    return httpx.Client(
        base_url=base_url,
        timeout=cfg.http_timeout,
        follow_redirects=kwargs.pop("follow_redirects", False),
        headers=headers,
        event_hooks={"response": [_log_response]},
        **kwargs,
    )


def bearer(token: str | Secret) -> dict[str, str]:
    value = token.reveal() if isinstance(token, Secret) else token
    return {"Authorization": f"Bearer {value}"}


# --- JWT (inspection only; the harness never verifies or creates valid signatures) --------


def _b64url_decode(part: str) -> bytes:
    return base64.urlsafe_b64decode(part + "=" * (-len(part) % 4))


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def jwt_claims(token: str) -> dict[str, Any]:
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("not a JWS compact token")
    return json.loads(_b64url_decode(parts[1]))


def jwt_tamper_signature(token: str) -> str:
    head, payload, sig = token.split(".")
    flipped = ("A" if sig[:1] != "A" else "B") + sig[1:]
    return f"{head}.{payload}.{flipped}"


def jwt_tamper_payload(token: str, **changes: Any) -> str:
    """Change claims but keep the original signature (must be rejected)."""
    head, payload, sig = token.split(".")
    claims = json.loads(_b64url_decode(payload))
    claims.update(changes)
    return f"{head}.{_b64url_encode(json.dumps(claims).encode())}.{sig}"


def jwt_alg_none(token: str) -> str:
    _, payload, _ = token.split(".")
    head = _b64url_encode(json.dumps({"alg": "none", "typ": "JWT"}).encode())
    return f"{head}.{payload}."


JWT_SHAPE = re.compile(r"^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$")


# --- Auth pacer ------------------------------------------------------------------------


class AuthPacer:
    """Keeps functional tests under the `auth` throttle (RATELIMIT_AUTH, default 10/minute).

    Every request this session sends to /api/auth/token/ or /api/auth/token/refresh/ (API or
    browser) calls :meth:`acquire` first. The pacer mirrors DRF's sliding window and sleeps
    until a slot is free, keeping ``margin`` slots in reserve. It never retries a 429 and never
    hides one: a 429 in a functional test is still a failure. The rate-limit tests use
    :meth:`used_in_window` to know how much of the window this session already consumed.
    """

    def __init__(self, rate: str, margin: int = 1, state_file: str | None = None) -> None:
        self.limit, self.window = parse_rate(rate)
        self.margin = margin
        self._calls: collections.deque[float] = collections.deque()
        self._lock = threading.Lock()
        # The server's window outlives a pytest session: back-to-back `make qa-remote` runs
        # share it. Wall-clock timestamps are persisted on the server so the next session
        # starts with the real count (found 2026-09-28: e2e run right after the API run hit 429).
        self._state_file = state_file
        self._load()

    def _load(self) -> None:
        if not self._state_file:
            return
        try:
            with open(self._state_file) as fh:
                stamps = json.load(fh)
        except (OSError, ValueError):
            return
        now = time.time()
        self._calls.extend(sorted(t for t in stamps if isinstance(t, (int, float)) and now - t < self.window))

    def _save(self) -> None:
        if not self._state_file:
            return
        try:
            with open(self._state_file, "w") as fh:
                json.dump(list(self._calls), fh)
        except OSError:
            pass

    def _prune(self, now: float) -> None:
        while self._calls and now - self._calls[0] >= self.window:
            self._calls.popleft()

    def used_in_window(self) -> int:
        with self._lock:
            self._prune(time.time())
            return len(self._calls)

    def acquire(self, reserve: bool = True) -> None:
        allowed = self.limit - (self.margin if reserve else 0)
        while True:
            with self._lock:
                now = time.time()
                self._prune(now)
                if len(self._calls) < allowed:
                    self._calls.append(now)
                    self._save()
                    return
                wait = self.window - (now - self._calls[0]) + 1.0
            log.info("auth pacer: waiting %.0fs to stay under the auth throttle", wait)
            time.sleep(wait)

    def record(self) -> None:
        """Record an auth call made without waiting (rate-limit tests)."""
        with self._lock:
            self._calls.append(time.time())
            self._save()


class AuthApi:
    """Thin client for the Identity contract that always goes through the pacer."""

    def __init__(self, client: httpx.Client, pacer: AuthPacer) -> None:
        self.client = client
        self.pacer = pacer

    def obtain(self, username: str, password: str | Secret, **extra: Any) -> httpx.Response:
        self.pacer.acquire()
        pwd = password.reveal() if isinstance(password, Secret) else password
        return self.client.post("/api/auth/token/", json={"username": username, "password": pwd, **extra})

    def obtain_raw(self, **kwargs: Any) -> httpx.Response:
        self.pacer.acquire()
        return self.client.post("/api/auth/token/", **kwargs)

    def refresh(self, refresh: str | None, **kwargs: Any) -> httpx.Response:
        self.pacer.acquire()
        if "json" not in kwargs and "content" not in kwargs:
            kwargs["json"] = {} if refresh is None else {"refresh": refresh}
        return self.client.post("/api/auth/token/refresh/", **kwargs)


def register_tokens(data: dict[str, Any]) -> None:
    for key in ("access", "refresh"):
        if isinstance(data.get(key), str):
            register(data[key])
