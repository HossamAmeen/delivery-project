#!/usr/bin/env bash
# Single restart entry point (hides the mode).
# Usage: restart.sh <backend|frontend|all> [--dry-run]
FLASH_SCRIPT=restart
set -euo pipefail
# shellcheck source=lib/common.sh
source "$(dirname "${BASH_SOURCE[0]}")/lib/common.sh"
# shellcheck source=lib/ops.sh
source "$FLASH_LIB_DIR/ops.sh"
trap ops_cleanup EXIT
target=""
while (($#)); do
  parse_common_flag "$1" && { shift; continue; }
  case "$1" in backend|frontend|all) target="$1"; shift ;; *) die "usage: restart.sh <backend|frontend|all> [--dry-run]" 2 ;; esac
done
[[ -n "$target" ]] || die "usage: restart.sh <backend|frontend|all> [--dry-run]" 2
ops_init
ops_lock
ops_guard_begin
case "$target" in
  backend) run_script restart-backend.sh ;;
  frontend) run_script restart-frontend.sh ;;
  all) run_script restart-backend.sh; run_script restart-frontend.sh ;;
esac
ops_guard_end
