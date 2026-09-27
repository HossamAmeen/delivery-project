#!/usr/bin/env bash
# Build the PWA LOCALLY (ADR-015: no node builds on the server) and copy dist/ into a release stage.
#   cd frontend && npm ci && VITE_API_BASE_URL=${VITE_API_BASE_URL} npm run build  → <out>/frontend/dist
# Usage: deploy-frontend.sh --out <stage dir> [--dry-run]     (FRONTEND_SRC_DIR overrides ./frontend)
FLASH_SCRIPT=deploy-frontend
set -euo pipefail
# shellcheck source=lib/common.sh
source "$(dirname "${BASH_SOURCE[0]}")/lib/common.sh"
out=""
while (($#)); do
  parse_common_flag "$1" && { shift; continue; }
  case "$1" in --out) [[ $# -ge 2 ]] || die "--out needs a directory" 2; out="$2"; shift 2 ;; *) die "unknown argument: $1" 2 ;; esac
done
[[ -n "$out" ]] || die "--out <stage dir> is required" 2
load_env
validate_mode
require_vars VITE_API_BASE_URL
src="${FRONTEND_SRC_DIR:-$REPO_ROOT/frontend}"
[[ -f "$src/package.json" && -f "$src/package-lock.json" ]] || die "$src/package.json / package-lock.json not found" 2
command -v npm >/dev/null || die "npm is not installed on this machine" 2
info "frontend build in $src (node $(node --version 2>/dev/null || echo '?'), VITE_API_BASE_URL=$VITE_API_BASE_URL)"
if is_dry_run; then
  log "[dry-run] (cd $src && npm ci && VITE_API_BASE_URL=$VITE_API_BASE_URL npm run build)"
  log "[dry-run] verify $src/dist/index.html contains id=\"app\"; copy $src/dist → $out/frontend/dist"
  exit 0
fi
(cd "$src" && run npm ci --no-audit --no-fund)
(cd "$src" && VITE_API_BASE_URL="$VITE_API_BASE_URL" run npm run build)
[[ -f "$src/dist/index.html" ]] || die "build produced no dist/index.html" 1
grep -q 'id="app"' "$src/dist/index.html" || die "dist/index.html has no id=\"app\" root" 1
mkdir -p "$out/frontend"
rm -rf "$out/frontend/dist"
cp -a "$src/dist" "$out/frontend/dist"
info "frontend dist staged: $(find "$out/frontend/dist" -type f | wc -l) files, $(du -sh "$out/frontend/dist" | cut -f1)"
