#!/usr/bin/env bash
# Create/update the QA users on the server (ADR-018) with random passwords generated ON THE SERVER:
#   qa_customer, qa_driver, qa_store, qa_admin (--staff --superuser), qa_inactive (--inactive; skipped
#   with a warning until create_role_user supports it, TASK-016). Passwords go to create_role_user on
#   stdin and to ${DEPLOY_PATH}/qa/credentials.env (0600) as QA_<ROLE>_USERNAME/PASSWORD; only usernames are printed.
# Usage: seed-qa-users.sh [--dry-run]
FLASH_SCRIPT=seed-qa-users
set -euo pipefail
# shellcheck source=lib/common.sh
source "$(dirname "${BASH_SOURCE[0]}")/lib/common.sh"
# shellcheck source=lib/ops.sh
source "$FLASH_LIB_DIR/ops.sh"
trap ops_cleanup EXIT
while (($#)); do parse_common_flag "$1" || die "unknown argument: $1" 2; shift; done
ops_init
ops_lock
ops_remote rw _fs_seed_qa_users
