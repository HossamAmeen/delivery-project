#!/usr/bin/env bash
# Render every Flash template (nginx http+full variants, systemd unit, shared.env skeleton) locally.
# Usage: deploy/scripts/render-templates.sh [--out <dir>] [--dry-run]
#   default <dir>: ${TMPDIR:-/tmp}/flash-render-<run-id>. Rendering is local and side-effect free,
#   so --dry-run renders too (it only affects scripts that change the server).
set -euo pipefail
FLASH_SCRIPT=render-templates
# shellcheck source=lib/common.sh
source "$(dirname "${BASH_SOURCE[0]}")/lib/common.sh"
# shellcheck source=lib/templates.sh
source "$FLASH_LIB_DIR/templates.sh"

out=""
while (($#)); do
  parse_common_flag "$1" && { shift; continue; }
  case "$1" in
    --out) [[ $# -ge 2 ]] || die "--out needs a directory" 2; out="$2"; shift 2 ;;
    -h|--help) sed -n '2,5p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) die "unknown argument: $1" 2 ;;
  esac
done
load_env
validate_mode
out="${out:-${TMPDIR:-/tmp}/flash-render-$(new_run_id)}"
render_all "$out"
info "rendered into $out:"
(cd "$out" && find . -type f | sort | sed 's|^\./|  |') >&2
printf '%s\n' "$out"
