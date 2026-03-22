#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./main_sync_guard_lib.sh
. "$script_dir/main_sync_guard_lib.sh"

main_sync_fetch_origin_main
head_sha="$(main_sync_head_sha)"
origin_main_sha="$(main_sync_origin_main_sha)"
merge_base_sha="$(main_sync_merge_base_sha)"
status="$(main_sync_status_from_commits "$head_sha" "$origin_main_sha" "$merge_base_sha")"

if is_main_sync_blocked_status "$status"; then
  printf 'Push blocked. %s\n' "$(main_sync_resolution_message "$status")" >&2
  exit 1
fi
