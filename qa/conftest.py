"""Root fixtures and hooks of the Flash QA harness.

- Configuration comes from the environment only (harness/config.py).
- The suite refuses to execute anywhere but the server (ADR-018, REQ-009). `--collect-only`
  works anywhere because no fixture runs during collection.
- Every test report is scrubbed of secrets, and the session fails if a secret reaches
  `.results/` (JUnit, log).
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import httpx
import pytest

from harness import config as qa_config
from harness.envelope import assert_success, describe
from harness.http import AuthApi, AuthPacer, bearer, make_client, register_tokens
from harness.secrets import count_secret_occurrences, redact

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / ".results"


# --------------------------------------------------------------------------------------
# Hooks
# --------------------------------------------------------------------------------------


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--dental-expect",
        action="store",
        default=None,
        help="baseline dental status codes 'url=code,url=code' to compare against (TASK-015)",
    )


def pytest_configure(config: pytest.Config) -> None:
    RESULTS.mkdir(exist_ok=True)
    # httpx logs full URLs at INFO (would include a query string); keep it quiet.
    for name in ("httpx", "httpcore", "asyncio", "urllib3"):
        logging.getLogger(name).setLevel(logging.WARNING)
    logging.getLogger("qa").setLevel(logging.INFO)


def _wants_ratelimit(config: pytest.Config) -> bool:
    return "ratelimit" in (config.option.markexpr or "")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    e2e_dir = ROOT / "e2e"
    for item in items:
        if e2e_dir in Path(str(item.path)).parents:
            item.add_marker(pytest.mark.e2e)

    # Rate-limit tests exhaust real throttle windows: run them only when selected
    # explicitly (`-m ratelimit`), and always last (ADR-018, test-strategy §7).
    if not _wants_ratelimit(config):
        keep, dropped = [], []
        for item in items:
            (dropped if item.get_closest_marker("ratelimit") else keep).append(item)
        if dropped:
            config.hook.pytest_deselected(items=dropped)
            items[:] = keep
    else:
        items.sort(key=lambda it: 1 if it.get_closest_marker("ratelimit") else 0)


def _redact_report(report: pytest.TestReport) -> None:
    longrepr = report.longrepr
    if longrepr is not None:
        if isinstance(longrepr, tuple) and len(longrepr) == 3:
            report.longrepr = (longrepr[0], longrepr[1], redact(longrepr[2]))
        else:
            text = str(longrepr)
            clean = redact(text)
            if clean != text:
                report.longrepr = clean
    if report.sections:
        report.sections = [(title, redact(content)) for title, content in report.sections]


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo):  # noqa: ARG001
    outcome = yield
    _redact_report(outcome.get_result())


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:  # noqa: ARG001
    """Evidence hygiene: no registered secret may be written to .results/ (TASK-015 AC)."""
    if session.config.option.collectonly or not RESULTS.exists():
        return
    leaks = []
    for path in RESULTS.rglob("*"):
        if path.is_file() and path.suffix in {".xml", ".log", ".txt", ".json"}:
            try:
                hits = count_secret_occurrences(path.read_text(errors="ignore"))
            except OSError:
                continue
            if hits:
                leaks.append(f"{path.relative_to(ROOT)}: {hits}")
    if leaks:
        session.config.get_terminal_writer().line(
            "SECRET HYGIENE FAILURE: registered secrets found in results files (counts only): " + "; ".join(leaks),
            red=True,
        )
        session.exitstatus = pytest.ExitCode.TESTS_FAILED


# --------------------------------------------------------------------------------------
# Configuration and the server-only guard
# --------------------------------------------------------------------------------------


@pytest.fixture(scope="session")
def cfg() -> qa_config.QAConfig:
    try:
        return qa_config.load()
    except qa_config.ConfigError as exc:
        pytest.exit(str(exc), returncode=pytest.ExitCode.USAGE_ERROR)


@pytest.fixture(scope="session", autouse=True)
def _server_only_guard(cfg: qa_config.QAConfig) -> None:
    """QA executes on the server only (REQ-009, ADR-018): refuse anywhere else."""
    if not os.path.isdir(os.path.join(cfg.deploy_path, "qa")):
        pytest.exit(
            f"{cfg.deploy_path}/qa not found: the QA suite runs on the server only "
            "(REQ-009, ADR-018). Use `make qa-remote ARGS=...` from the repository root.",
            returncode=pytest.ExitCode.USAGE_ERROR,
        )


@pytest.fixture(scope="session")
def results_dir() -> Path:
    RESULTS.mkdir(exist_ok=True)
    return RESULTS


def _need(func, *args):
    try:
        return func(*args)
    except qa_config.ConfigError as exc:
        pytest.fail(str(exc), pytrace=False)


@pytest.fixture(scope="session")
def health_token(cfg: qa_config.QAConfig):
    return _need(cfg.health_token)


@pytest.fixture(scope="session")
def creds(cfg: qa_config.QAConfig):
    """Factory: ``creds("CUSTOMER")`` -> RoleCredentials (fails clearly when not seeded)."""
    return lambda role: _need(cfg.credentials, role)


# --------------------------------------------------------------------------------------
# HTTP clients
# --------------------------------------------------------------------------------------


@pytest.fixture(scope="session")
def api(cfg: qa_config.QAConfig):
    with make_client(cfg.base_url, cfg) as client:
        yield client


@pytest.fixture(scope="session")
def web(cfg: qa_config.QAConfig):
    with make_client(cfg.web_url, cfg, headers={"Accept": "text/html,*/*"}) as client:
        yield client


@pytest.fixture
def fresh_api(cfg: qa_config.QAConfig):
    """A client with an empty cookie jar (admin session tests)."""
    with make_client(cfg.base_url, cfg) as client:
        yield client


@pytest.fixture(scope="session")
def auth_pacer(cfg: qa_config.QAConfig) -> AuthPacer:
    return AuthPacer(cfg.rate_auth)


@pytest.fixture(scope="session")
def auth_api(api: httpx.Client, auth_pacer: AuthPacer) -> AuthApi:
    return AuthApi(api, auth_pacer)


@pytest.fixture(scope="session")
def tokens(auth_api: AuthApi, creds):
    """Factory: ``tokens("DRIVER")`` -> {"access", "refresh"}; one login per role per session."""
    cache: dict[str, dict[str, str]] = {}

    def get(role: str) -> dict[str, str]:
        role = role.upper()
        if role not in cache:
            c = creds(role)
            resp = auth_api.obtain(c.username, c.password)
            if resp.status_code != 200:
                pytest.fail(f"login as QA {role} user failed: {describe(resp)}", pytrace=False)
            data = assert_success(resp)
            register_tokens(data)
            cache[role] = data
        return cache[role]

    return get


@pytest.fixture(scope="session")
def auth_headers(tokens):
    """Factory: ``auth_headers("ADMIN")`` -> Authorization header dict."""
    return lambda role: bearer(tokens(role)["access"])
