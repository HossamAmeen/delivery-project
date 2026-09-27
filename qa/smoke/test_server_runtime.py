"""Server runtime checks, executed ON the server by `make qa-remote` as user `hossam`
(FEAT-004 AC4, AC8, AC9, AC10, AC11; ADR-015, ADR-017). Read-only: no sudo, no writes,
never reads the content of an env/credentials file (only its mode), never touches dental.

Checks that need sudo (nginx file hashes, Flash nginx logs, certbot) are manual steps in the
FEAT-004 plan; tests here skip with a reason when the data is not readable as `hossam`.
Plan: FEAT-004 TC-004-RUN-01..12.
"""

import os
import shutil
import socket
import stat
import subprocess

import pytest

from harness.envelope import check
from harness.secrets import count_secret_occurrences

pytestmark = [pytest.mark.deploy, pytest.mark.regression]


def _run(*cmd: str, timeout: int = 20) -> subprocess.CompletedProcess:
    if shutil.which(cmd[0]) is None:
        pytest.skip(f"{cmd[0]} not available on this host")
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)


def _systemctl(*args: str) -> str:
    return _run("systemctl", *args).stdout.strip()


def _primary_ip() -> str:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(("192.0.2.1", 9))  # TEST-NET-1: no packet is sent for a UDP connect
        return s.getsockname()[0]


def _port_open(ip: str, port: int, timeout: float = 3.0) -> bool:
    try:
        with socket.create_connection((ip, port), timeout=timeout):
            return True
    except OSError:
        return False


def test_backend_service_active_enabled_restart_always(cfg):
    """TC-004-RUN-01 (AC4): flash-backend active, enabled, Restart=always, MemoryMax bounded."""
    svc = cfg.backend_service
    check(_systemctl("is-active", svc) == "active", f"{svc} is not active")
    check(_systemctl("is-enabled", svc) == "enabled", f"{svc} is not enabled (would not survive a reboot)")
    check(_systemctl("show", svc, "-p", "Restart", "--value") == "always", f"{svc} Restart is not 'always'")
    mem = _systemctl("show", svc, "-p", "MemoryMax", "--value")
    check(mem not in ("", "infinity"), f"{svc} has no MemoryMax (resource guard, ADR-015)")


def test_backend_binds_loopback_only(cfg):
    """TC-004-RUN-02 (AC4): gunicorn bound to 127.0.0.1:<port>; not reachable on other addresses."""
    port = cfg.backend_port
    check(_port_open("127.0.0.1", port), f"nothing listens on 127.0.0.1:{port}")
    check(not _port_open(_primary_ip(), port), f"port {port} reachable on the primary interface address")
    if cfg.server_public_ip:
        check(not _port_open(cfg.server_public_ip, port), f"port {port} reachable on the public IP")
    exec_start = _systemctl("show", cfg.backend_service, "-p", "ExecStart", "--value")
    check(f"127.0.0.1:{port}" in exec_start, f"ExecStart does not bind 127.0.0.1:{port}")


def test_listening_sockets_for_backend_port_are_loopback(cfg):
    """TC-004-RUN-03: `ss -ltn` shows the backend port only on 127.0.0.1."""
    out = _run("ss", "-ltnH").stdout
    locals_ = [line.split()[3] for line in out.splitlines() if len(line.split()) >= 4 and line.split()[3].endswith(f":{cfg.backend_port}")]
    check(bool(locals_), f"no listener on port {cfg.backend_port}")
    check(all(addr.startswith("127.0.0.1:") for addr in locals_), f"non-loopback listeners: {locals_}")


def test_dental_service_still_active(cfg):
    """TC-004-RUN-04 (AC9): dental-clinic-backend is active (status query only)."""
    if not cfg.dental_service:
        pytest.skip("QA_DENTAL_SERVICE empty")
    check(_systemctl("is-active", cfg.dental_service) == "active", f"{cfg.dental_service} is not active")


def test_release_layout(cfg):
    """TC-004-RUN-05 (AC8): current -> releases/<id> with REVISION; shared/{db,media,...} outside releases."""
    base = cfg.deploy_path
    current = os.path.join(base, "current")
    check(os.path.islink(current), "current is not a symlink")
    target = os.path.realpath(current)
    check(os.path.dirname(target) == os.path.realpath(os.path.join(base, "releases")), "current does not point into releases/")
    check(os.path.isfile(os.path.join(target, "REVISION")), "REVISION missing in the current release")
    check(os.path.isfile(os.path.join(target, "frontend", "dist", "index.html")), "frontend/dist/index.html missing in the current release")
    for sub in ("db", "cache", "static", "media", "logs", "backups"):
        check(os.path.isdir(os.path.join(base, "shared", sub)), f"shared/{sub} missing")
    check(os.path.isfile(os.path.join(base, "shared", "db", "flash.sqlite3")), "SQLite DB not in shared/db (ADR-017)")


@pytest.mark.security
def test_secret_files_mode_0600(cfg):
    """TC-004-RUN-06 (AC11): shared/.env and qa/credentials.env are 0600 (mode only, never read)."""
    for rel in ("shared/.env", "qa/credentials.env"):
        path = os.path.join(cfg.deploy_path, rel)
        check(os.path.isfile(path), f"{rel} missing")
        mode = stat.S_IMODE(os.stat(path).st_mode)
        check(mode == 0o600, f"{rel} mode is {oct(mode)}, expected 0o600")


def test_retention_within_limits(cfg):
    """TC-004-RUN-07 (AC10): releases <= RELEASES_TO_KEEP, pre-migrate DB backups <= DB_BACKUPS_TO_KEEP."""
    releases = [d for d in os.listdir(os.path.join(cfg.deploy_path, "releases")) if not d.startswith(".")]
    check(len(releases) <= cfg.releases_to_keep, f"{len(releases)} releases kept (max {cfg.releases_to_keep})")
    backups = [f for f in os.listdir(os.path.join(cfg.deploy_path, "shared", "backups")) if f.startswith("flash-") and f.endswith(".sqlite3")]
    check(len(backups) <= cfg.db_backups_to_keep, f"{len(backups)} DB backups kept (max {cfg.db_backups_to_keep})")


def test_disk_and_memory_budget(cfg, results_dir):
    """TC-004-RUN-08 (AC10): free disk on the deploy path >= MIN_FREE_DISK_MB; memory recorded."""
    free_mb = shutil.disk_usage(cfg.deploy_path).free // (1024 * 1024)
    meminfo = {}
    try:
        with open("/proc/meminfo") as fh:
            for line in fh:
                key, _, rest = line.partition(":")
                meminfo[key] = int(rest.split()[0]) // 1024
    except OSError:
        pass
    (results_dir / "resources.txt").write_text(
        f"free_disk_mb={free_mb}\nmem_total_mb={meminfo.get('MemTotal')}\nmem_available_mb={meminfo.get('MemAvailable')}\n"
        f"swap_total_mb={meminfo.get('SwapTotal')}\n"
    )
    check(free_mb >= cfg.min_free_disk_mb, f"only {free_mb} MB free on {cfg.deploy_path} (min {cfg.min_free_disk_mb})")


def test_no_celery_or_redis_units(cfg):
    """TC-004-RUN-09 (FEAT-001 AC10): no Flash Celery units and no Redis listening."""
    units = _run("systemctl", "list-units", "--all", "--no-legend", "--plain", "flash-*").stdout
    check("celery" not in units.lower(), "a Flash Celery unit exists (CELERY_ENABLED=False, ADR-017)")
    check(not _port_open("127.0.0.1", 6379, timeout=1), "something listens on the Redis port 6379 (no Redis on this server)")


@pytest.mark.security
def test_backend_journal_has_no_secrets(cfg, health_token, creds):
    """TC-004-RUN-10 (AC7, AC11): count-only scan of `journalctl -u flash-backend` (last 24 h)."""
    # The fixtures register the health token and the QA passwords as secrets on creation.
    for role in ("CUSTOMER", "DRIVER", "STORE", "ADMIN"):
        creds(role)  # registers the passwords
    proc = _run("journalctl", "-u", cfg.backend_service, "--since", "-24h", "--no-pager", "-o", "cat", timeout=60)
    if proc.returncode != 0 or "No journal files were found" in proc.stderr or "not seeing messages" in proc.stderr:
        pytest.skip("journal not readable as the QA user; run the sudo count-only grep from the FEAT-004 plan (TC-004-MAN-06)")
    check(count_secret_occurrences(proc.stdout) == 0, "a registered secret (health token or QA password) appears in the flash-backend journal")
    check("password=" not in proc.stdout, "a password= query string appears in the flash-backend journal")


@pytest.mark.security
def test_flash_nginx_logs_have_no_secrets(cfg, health_token):
    """TC-004-RUN-11 (AC11): count-only scan of the Flash nginx logs, if readable without sudo.
    (`health_token` is requested so the token is registered for the scan.)"""
    paths = ["/var/log/nginx/flash-api.access.log", "/var/log/nginx/flash-web.access.log"]
    readable = [p for p in paths if os.access(p, os.R_OK)]
    if not readable:
        pytest.skip("Flash nginx logs not readable as the QA user; run the sudo count-only grep (TC-004-MAN-06)")
    for p in readable:
        with open(p, errors="ignore") as fh:
            text = fh.read()
        check(count_secret_occurrences(text) == 0, f"a registered secret appears in {p}")


def test_dental_path_untouched_by_flash(cfg):
    """TC-004-RUN-12 (AC9): the Flash deploy path is not under the dental path; port differs from 8000."""
    check(not os.path.realpath(cfg.deploy_path).startswith("/srv/dental-clinic"), "Flash deploy path is under /srv/dental-clinic")
    check(cfg.backend_port != 8000, "Flash backend port collides with dental's 8000")


def test_release_runs_python_313(cfg, results_dir):
    """TC-004-RUN-13 (FEAT-001 AC1, FEAT-004 AC4; ADR-016): the current release venv is Python 3.13
    and the unit starts gunicorn from it."""
    python = os.path.join(cfg.deploy_path, "current", "venv", "bin", "python")
    check(os.path.exists(python), "current/venv/bin/python missing")
    version = subprocess.run([python, "--version"], capture_output=True, text=True, timeout=20, check=False).stdout.strip()
    (results_dir / "release-python.txt").write_text(version + "\n")
    check(version.startswith("Python 3.13"), f"release venv runs {version!r}, expected Python 3.13.x")
    exec_start = _systemctl("show", cfg.backend_service, "-p", "ExecStart", "--value")
    check("/current/venv/bin/gunicorn" in exec_start, "ExecStart does not run gunicorn from current/venv")


def test_previous_pointer_and_no_leftover_backups(cfg):
    """TC-004-RUN-14 (TASK-017): the current release records PREVIOUS (an existing release, 0644),
    and no safe-apply nginx backup directories are left in /tmp."""
    import glob

    current = os.path.realpath(os.path.join(cfg.deploy_path, "current"))
    prev_file = os.path.join(current, "PREVIOUS")
    check(os.path.isfile(prev_file), "current release has no PREVIOUS file")
    check(stat.S_IMODE(os.stat(prev_file).st_mode) == 0o644, "PREVIOUS is not mode 0644")
    with open(prev_file) as fh:
        prev = fh.read().strip()
    check(os.path.isdir(os.path.join(cfg.deploy_path, "releases", prev)), f"PREVIOUS names a missing release {prev!r}")
    leftovers = glob.glob("/tmp/flash-nginx-backup-*")
    check(not leftovers, f"leftover nginx backup dirs in /tmp: {leftovers}")
