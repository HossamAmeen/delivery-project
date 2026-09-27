#!/usr/bin/env bash
# Server-side build of an uploaded release: uv venv (PYTHON_VERSION) + uv pip install
# -r backend/requirements/production.txt → manage.py check --deploy → collectstatic --noinput.
# Called by deploy.sh (migrations are migrate.sh). Usage: deploy-backend.sh --release <id> [--dry-run]
FLASH_SCRIPT=deploy-backend
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
[[ "$release" =~ ^[0-9]{8}-[0-9]{6}$ ]] || die "--release <YYYYMMDD-HHMMSS> is required" 2
ops_init
ops_remote rw _fs_venv_install "$release"
ops_remote rw _fs_check_deploy "$release"
ops_remote rw _fs_collectstatic "$release"
