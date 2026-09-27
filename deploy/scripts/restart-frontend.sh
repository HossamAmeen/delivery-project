#!/usr/bin/env bash
# "Restart" the static frontend: re-render the web site file, nginx safe-apply with a forced reload
# (nginx -t first; the previous file is restored on failure). There is no frontend process.
# Usage: restart-frontend.sh [--dry-run]
FLASH_SCRIPT=restart-frontend
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
variant="$(ops_remote ro _fs_cert_state)"
ops_render
web="$(ops_mktemp web)"; cp "$OPS_RENDER_DIR/nginx/$variant/$WEB_DOMAIN" "$web/"
info "web site variant: $variant (sha $(sha_of "$web/$WEB_DOMAIN" | cut -c1-12))"
ops_stage_upload "$web"
ops_remote rw _fs_nginx_safe_apply "$OPS_STAGE" 1 || { ops_stage_cleanup; die "nginx safe-apply failed (previous file restored, nginx not reloaded)" 1; }
ops_stage_cleanup
ops_guard_end
