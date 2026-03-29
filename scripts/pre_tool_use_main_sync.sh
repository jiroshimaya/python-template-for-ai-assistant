#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./main_sync_guard_lib.sh
. "$script_dir/main_sync_guard_lib.sh"

ensure_main_sync_jq

input="$(cat)"
cwd="$(printf '%s' "$input" | jq -r '.cwd // empty')"
tool_name="$(printf '%s' "$input" | jq -r '.toolName // .tool // empty')"

if [ -z "$cwd" ] || [ ! -d "$cwd" ]; then
  echo "main sync guard の実行ディレクトリが不正です: $cwd" >&2
  exit 1
fi

state_json_path="$cwd/$MAIN_SYNC_STATE_JSON_REL"
if [ ! -f "$state_json_path" ]; then
  exit 0
fi

cd "$cwd"
status="$(refresh_main_sync_state_from_local_refs "$cwd" "$state_json_path")"
if [ -z "$status" ]; then
  echo "main sync guard の state ファイルに status がありません: $state_json_path" >&2
  exit 1
fi

if ! is_main_sync_blocked_status "$status"; then
  exit 0
fi

if ! is_main_sync_denied_tool "$tool_name"; then
  exit 0
fi

reason="$(main_sync_resolution_message "$status")"
jq -cn \
  --arg reason "$reason" \
  '{
    permissionDecision: "deny",
    permissionDecisionReason: $reason
  }'
