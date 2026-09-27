"""Dental-clinic sites keep responding (FEAT-004 AC9; ADR-015). Read-only GETs only.

Each run writes a snapshot of the status codes to .results/dental-<UTC>.json (evidence).
With `--dental-expect="<url>=<code>,<url>=<code>"` (codes from the baseline run, passed
through `make qa-remote ARGS=...`) the run also asserts the codes are identical to that
baseline (before/after a deploy or rollback, TASK-015). The nginx file
hashes and `systemctl is-active` are compared in test_server_runtime.py and in the manual
steps of the FEAT-004 plan.
Plan: FEAT-004 TC-004-DEN-01..02.
"""

import datetime as dt
import json

import httpx
import pytest

from harness.envelope import check

pytestmark = [pytest.mark.smoke, pytest.mark.deploy, pytest.mark.regression]


def _snapshot(cfg) -> dict[str, object]:
    codes: dict[str, object] = {}
    with httpx.Client(timeout=cfg.http_timeout, follow_redirects=False, headers={"User-Agent": "flash-qa-harness/1.0"}) as client:
        for url in cfg.dental_urls:
            try:
                codes[url] = client.get(url).status_code
            except httpx.HTTPError as exc:
                codes[url] = f"error: {type(exc).__name__}"
    return codes


def test_dental_sites_reachable(cfg, results_dir):
    """TC-004-DEN-01: every dental URL answers over HTTPS without a 5xx or connection error."""
    codes = _snapshot(cfg)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    (results_dir / f"dental-{stamp}.json").write_text(json.dumps({"taken_at": stamp, "status": codes}, indent=2))
    for url, code in codes.items():
        check(isinstance(code, int) and code < 500, f"dental {url} -> {code}")


def test_dental_status_matches_baseline(cfg, request):
    """TC-004-DEN-02: identical status codes to the pre-deploy/pre-rollback baseline."""
    expect = request.config.getoption("dental_expect")
    if not expect:
        pytest.skip("--dental-expect not given (this is a baseline run)")
    baseline: dict[str, object] = {}
    for pair in expect.split(","):
        url, _, code = pair.strip().rpartition("=")
        baseline[url] = int(code) if code.isdigit() else code
    check(_snapshot(cfg) == baseline, f"dental status codes differ from the baseline {baseline}")
