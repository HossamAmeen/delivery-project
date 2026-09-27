#!/usr/bin/env bash
# Read-only views of the server.
# Usage: status.sh status
#        status.sh logs [<lines>] [--follow]      (journald of ${BACKEND_SYSTEMD_SERVICE})
FLASH_SCRIPT=status
set -euo pipefail
# shellcheck source=lib/common.sh
source "$(dirname "${BASH_SOURCE[0]}")/lib/common.sh"
# shellcheck source=lib/ops.sh
source "$FLASH_LIB_DIR/ops.sh"
cmd="${1:-status}"; [[ $# -gt 0 ]] && shift
ops_init
case "$cmd" in
  status) ops_remote ro _fs_status ;;
  logs)
    lines=200; follow=0
    while (($#)); do
      case "$1" in --follow) follow=1 ;; [0-9]*) lines="$1" ;; --dry-run) ;; *) die "unknown argument: $1" 2 ;; esac
      shift
    done
    ops_remote ro _fs_logs "$lines" "$follow" ;;
  -h|--help) sed -n '2,4p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//' ;;
  *) die "usage: status.sh status | logs [<lines>] [--follow]" 2 ;;
esac
