#!/usr/bin/env bash
# Restart the Flash backend unit and wait for the local health checks (HEALTH_CHECK_TIMEOUT).
# Usage: restart-backend.sh [--dry-run]
FLASH_SCRIPT=restart-backend
set -euo pipefail
# shellcheck source=lib/common.sh
source "$(dirname "${BASH_SOURCE[0]}")/lib/common.sh"
# shellcheck source=lib/ops.sh
source "$FLASH_LIB_DIR/ops.sh"
trap ops_cleanup EXIT
while (($#)); do parse_common_flag "$1" || die "unknown argument: $1" 2; shift; done
ops_init
ops_lock
ops_guard_begin
ops_remote rw _fs_restart_backend
run_script health-check.sh --local-only --timeout "$HEALTH_CHECK_TIMEOUT" || { print_rollback_hint; exit 1; }
ops_guard_end
