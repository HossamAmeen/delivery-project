"""Rate limits return 429 in the standard envelope (FEAT-001 AC5; DRF_SKILL §61–83; ADR-017).

Run ONLY as its own session, LAST, with a throttle reset before and after:

    make throttle-reset && make qa-remote ARGS="-m ratelimit" ; make throttle-reset

(conftest deselects these tests unless `-m` names `ratelimit`.)

Each test sends exactly `limit` allowed requests and asserts request `limit + 1` is throttled.
Because the requests go through nginx to 2 gunicorn workers, a 429 at exactly `limit + 1`
also proves the counters are shared across workers (FileBasedCache, ADR-017); a per-worker
cache would let roughly twice the limit through.
Limits come from QA_RATELIMIT_* (defaults = the documented server values).
Plan: FEAT-001 TC-001-RL-01..05.
"""

import time

import pytest

from harness.config import parse_rate
from harness.envelope import assert_throttled, check, describe
from harness.http import bearer

pytestmark = [pytest.mark.ratelimit, pytest.mark.regression, pytest.mark.security]

MAX_LIMIT = 1000  # refuse to hammer the shared server if a limit is misconfigured


def _burst(send, limit: int, allowed_statuses: set[int], label: str) -> None:
    check(0 < limit <= MAX_LIMIT, f"{label}: refusing a burst of {limit} requests")
    for i in range(1, limit + 1):
        resp = send()
        check(resp.status_code != 429, f"{label}: request {i}/{limit} throttled too early: {describe(resp)}")
        check(resp.status_code in allowed_statuses, f"{label}: request {i} unexpected: {describe(resp)}")
    resp = send()
    check(resp.status_code == 429, f"{label}: request {limit + 1} was not throttled: {describe(resp)}")
    assert_throttled(resp)


def test_auth_scope_is_throttled(api, auth_pacer, tokens, cfg):
    """TC-001-RL-01: /api/auth/token/ (auth scope, stricter) -> 429 after RATELIMIT_AUTH."""
    tokens("CUSTOMER")  # the user-scope test below needs a token obtained before auth is exhausted
    # Let this session's earlier auth calls leave the sliding window so the count starts at 0.
    while auth_pacer.used_in_window():
        time.sleep(2)
    limit, _ = parse_rate(cfg.rate_auth)

    def send():
        auth_pacer.record()
        return api.post("/api/auth/token/", json={"username": "qa_rl_nobody", "password": "qa-rl-wrong"})

    _burst(send, limit, {401}, "auth")
    # The refresh endpoint shares the auth scope: it is throttled now too.
    auth_pacer.record()
    assert_throttled(api.post("/api/auth/token/refresh/", json={"refresh": "x"}))


def test_auth_scope_is_stricter_than_user_scope(cfg):
    """TC-001-RL-02: configuration sanity — auth rate per second < user rate per second."""
    a, a_s = parse_rate(cfg.rate_auth)
    u, u_s = parse_rate(cfg.rate_user)
    check(a / a_s < u / u_s, "auth scope must be stricter than the user scope")


def test_user_scope_is_throttled(api, tokens, cfg):
    """TC-001-RL-03: authenticated requests (user scope) -> 429 after RATELIMIT_USER."""
    headers = bearer(tokens("CUSTOMER")["access"])
    limit, _ = parse_rate(cfg.rate_user)
    _burst(lambda: api.get("/api/users/me/", headers=headers), limit, {200}, "user")


def test_health_scope_is_throttled(api, cfg, health_token):
    """TC-001-RL-04: /api/status/ + /api/health/ share the health scope -> 429 after RATELIMIT_HEALTH."""
    limit, _ = parse_rate(cfg.rate_health)
    _burst(lambda: api.get("/api/status/"), limit, {200}, "health")
    assert_throttled(api.get("/api/health/", headers={"X-Health-Check-Token": health_token.reveal()}))


def test_anon_scope_is_throttled(api, cfg):
    """TC-001-RL-05: anonymous scope -> 429 after RATELIMIT_ANON.

    The Foundation contract has no public endpoint that uses the default anon scope
    (/api/status/ and /api/health/ use `health`; /api/auth/* use `auth`; anonymous calls to
    protected views fail authentication before throttling). Set QA_ANON_THROTTLE_PATH to a
    public anon-scoped GET path once the TL names one (test-strategy §12).
    """
    if not cfg.anon_throttle_path:
        pytest.skip("no anon-scope endpoint in the Foundation contract (QA_ANON_THROTTLE_PATH unset) — see test-strategy §12")
    limit, _ = parse_rate(cfg.rate_anon)
    _burst(lambda: api.get(cfg.anon_throttle_path), limit, {200, 404}, "anon")
