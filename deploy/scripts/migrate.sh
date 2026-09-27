#!/usr/bin/env bash
# Migrations (ADR-013 forward-only, ADR-017 SQLite backup first) for a release (default: current).
#   migrate --plan (printed) → online backup of the DB to shared/backups (if it exists) → migrate --noinput
#   → append "at=… backup=… applied=yes|no" to releases/<id>/MIGRATION_STATE → prune backups.
# Usage: migrate.sh [--release <id>] [--dry-run]
FLASH_SCRIPT=migrate
set -euo pipefail
# shellcheck source=lib/common.sh
source "$(dirname "${BASH_SOURCE[0]}")/lib/common.sh"
# shellcheck source=lib/ops.sh
source "$FLASH_LIB_DIR/ops.sh"
trap ops_cleanup EXIT
release=""
while (($#)); do
  parse_common_flag "$1" && { shift; continue; }
  case "$1" in --release) [[ $# -ge 2 ]] || die "--release needs an id" 2; release="$2"; shift 2 ;; *) die "unknown argument: $1" 2 ;; esac
done
ops_init
ops_lock
if [[ -z "$release" ]]; then
  release="$(ops_remote ro _fs_current_id)" || die "no current release on the server (deploy first)" 1
fi
[[ "$release" =~ ^[0-9]{8}-[0-9]{6}$ ]] || die "invalid release id '$release'" 2
info "migrate: release $release"
ops_remote rw _fs_migrate "$release"
