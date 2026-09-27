#!/usr/bin/env bash
# Flash health check (ADR-015), run on the server over SSH. Read-only.
#   systemctl is-active ${BACKEND_SYSTEMD_SERVICE}; GET http://127.0.0.1:${BACKEND_PORT}/api/health/ and /ready/;
#   the same through https://${API_DOMAIN}; https://${API_DOMAIN}/api/status/; https://${WEB_DOMAIN}/ (200 + id="app");
#   sudo nginx -t. Token: X-Health-Check-Token from shared/.env via curl -H @- (never argv, output or logs).
# Usage: health-check.sh [--timeout <s>] [--local-only] [--dry-run]
#   --timeout  retry every 5 s until all checks pass or <s> elapse (default: one attempt)
#   --local-only  unit + 127.0.0.1 checks only (used right after a restart)
# Exit: 0 all pass · 1 a check failed (named in the output) · 2 config error.
FLASH_SCRIPT=health-check
set -euo pipefail
# shellcheck source=lib/common.sh
source "$(dirname "${BASH_SOURCE[0]}")/lib/common.sh"
# shellcheck source=lib/ops.sh
source "$FLASH_LIB_DIR/ops.sh"
trap ops_cleanup EXIT
usage() { sed -n "2,/^set -euo/p" "${BASH_SOURCE[0]}" | sed "\$d" | sed "s/^# \\{0,1\\}//"; }

timeout_s=0; local_only=0
while (($#)); do
  parse_common_flag "$1" && { shift; continue; }
  case "$1" in
    --timeout) [[ $# -ge 2 && "$2" =~ ^[0-9]+$ ]] || die "--timeout needs seconds" 2; timeout_s="$2"; shift 2 ;;
    --local-only) local_only=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) die "unknown argument: $1" 2 ;;
  esac
done
ops_init
if is_dry_run; then
  log "[dry-run] remote($(ssh_target)) read-only checks: is-active $BACKEND_SYSTEMD_SERVICE; 127.0.0.1:$BACKEND_PORT/api/health/{,ready/} (header token via stdin)$([[ $local_only == 1 ]] || echo "; https://$API_DOMAIN/api/health/{,ready/}, /api/status/; https://$WEB_DOMAIN/ (id=\"app\"); sudo nginx -t") — retry up to ${timeout_s}s"
  exit 0
fi
deadline=$(( $(date +%s) + timeout_s )); attempt=0
while :; do
  attempt=$((attempt + 1))
  if out="$(ops_remote ro _fs_health "$local_only")"; then
    printf '%s\n' "$out" >&2; info "health: ALL CHECKS PASSED (attempt $attempt)"; exit 0
  fi
  if (( $(date +%s) >= deadline )); then
    printf '%s\n' "$out" >&2
    err "health: FAILED after $attempt attempt(s): $(grep '^FAIL' <<< "$out" | sed 's/^FAIL  //' | paste -sd ';' -)"
    exit 1
  fi
  info "health: not yet ($(grep -c '^FAIL' <<< "$out") failing) — retrying in 5 s"
  sleep 5
done
