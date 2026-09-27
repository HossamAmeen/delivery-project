#!/usr/bin/env bash
# collectstatic --noinput for a release (default: current) into ${DEPLOY_PATH}/shared/static.
# Usage: collectstatic.sh [--release <id>] [--dry-run]
FLASH_SCRIPT=collectstatic
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
if [[ -z "$release" ]]; then
  release="$(ops_remote ro _fs_current_id)" || die "no current release on the server (deploy first)" 1
fi
[[ "$release" =~ ^[0-9]{8}-[0-9]{6}$ ]] || die "invalid release id '$release'" 2
ops_remote rw _fs_collectstatic "$release"
