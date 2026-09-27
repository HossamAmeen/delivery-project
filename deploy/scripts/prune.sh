#!/usr/bin/env bash
# Retention: keep RELEASES_TO_KEEP releases (never current or its previous) and DB_BACKUPS_TO_KEEP
# backups of each kind (never the one the current release's MIGRATION_STATE references).
# Usage: prune.sh [--dry-run]
FLASH_SCRIPT=prune
set -euo pipefail
# shellcheck source=lib/common.sh
source "$(dirname "${BASH_SOURCE[0]}")/lib/common.sh"
# shellcheck source=lib/ops.sh
source "$FLASH_LIB_DIR/ops.sh"
trap ops_cleanup EXIT
while (($#)); do parse_common_flag "$1" || die "unknown argument: $1" 2; shift; done
ops_init
ops_lock
ops_remote rw _fs_prune_releases
ops_remote rw _fs_prune_backups
