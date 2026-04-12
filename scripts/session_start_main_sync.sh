#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./main_sync_guard_lib.sh
. "$script_dir/main_sync_guard_lib.sh"

ensure_main_sync_jq

input="$(cat)"
cwd="$(printf '%s' "$input" | jq -r '.cwd // empty')"

if [ -z "$cwd" ] || [ ! -d "$cwd" ]; then
  echo "main sync guard の実行ディレクトリが不正です: $cwd" >&2
  exit 1
fi

cd "$cwd"
main_sync_fetch_origin_main
head_sha="$(main_sync_head_sha)"
origin_main_sha="$(main_sync_origin_main_sha)"
merge_base_sha="$(main_sync_merge_base_sha)"
status="$(main_sync_status_from_commits "$head_sha" "$origin_main_sha" "$merge_base_sha")"
write_main_sync_state "$cwd" "$status" "$head_sha" "$origin_main_sha" "$merge_base_sha"
