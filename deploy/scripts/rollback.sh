#!/usr/bin/env bash
# Roll back to the previous release (or --to <id>) — ADR-013 + ADR-017.
#   switch current → (DB restore when decided) → restart → health (HEALTH_CHECK_TIMEOUT) → dental compare.
#   DB restore (SQLite): ROLLBACK_RESTORE_DB=auto|always|never (default auto = restore only if the release
#   being rolled back applied migrations), overridden by --restore-db / --no-restore-db / --restore-mode <m>.
#   Restoring stops the unit, saves the current DB as shared/backups/pre-rollback-<ts>.sqlite3, copies the
#   release's pre-migrate backup back, starts the unit. WRITES MADE AFTER THAT DEPLOY ARE LOST.
#   Reverse migrations are never run.
# Usage: rollback.sh [--to <release-id>] [--restore-db | --no-restore-db | --restore-mode auto|always|never] [--dry-run]
FLASH_SCRIPT=rollback
set -euo pipefail
# shellcheck source=lib/common.sh
source "$(dirname "${BASH_SOURCE[0]}")/lib/common.sh"
# shellcheck source=lib/ops.sh
source "$FLASH_LIB_DIR/ops.sh"
trap ops_cleanup EXIT

to=""; mode=""
while (($#)); do
  parse_common_flag "$1" && { shift; continue; }
  case "$1" in
    --to) [[ $# -ge 2 ]] || die "--to needs a release id" 2; to="$2"; shift 2 ;;
    --restore-db) mode=always; shift ;;
    --no-restore-db) mode=never; shift ;;
    --restore-mode) [[ $# -ge 2 ]] || die "--restore-mode needs auto|always|never" 2; mode="$2"; shift 2 ;;
    -h|--help) sed -n '2,11p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) die "unknown argument: $1" 2 ;;
  esac
done
ops_init
mode="${mode:-${ROLLBACK_RESTORE_DB:-auto}}"
case "$mode" in auto|always|never) ;; *) die "restore mode must be auto|always|never (got '$mode')" 2 ;; esac
[[ -z "$to" || "$to" =~ ^[0-9]{8}-[0-9]{6}$ ]] || die "invalid release id '$to'" 2
ops_lock
ops_guard_begin
ops_remote ro _fs_release_info >&2
if is_dry_run; then
  ops_remote ro _fs_rollback "$to" "$mode" 1 >&2 || die "rollback is not possible (see above)" 1
  run_script health-check.sh --timeout "$HEALTH_CHECK_TIMEOUT"
  ops_guard_end
  exit 0
fi
out="$(ops_remote rw _fs_rollback "$to" "$mode" 2>&1)" && rc=0 || rc=$?
printf '%s\n' "$out" >&2
[[ $rc == 0 ]] || die "rollback FAILED (exit $rc) — see above; the site may need manual attention" 1
info "$(grep '^ROLLBACK_RESULT' <<< "$out" || true)"
if ! run_script health-check.sh --timeout "$HEALTH_CHECK_TIMEOUT"; then
  ops_guard_end
  die "rolled back, but the health check FAILS — investigate (journalctl -u $BACKEND_SYSTEMD_SERVICE)" 1
fi
ops_guard_end
info "rollback complete"
