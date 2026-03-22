#!/usr/bin/env bash

set -u -o pipefail

protected_path="pyproject.toml"
allow_env_var="COPILOT_ALLOW_PYPROJECT_TOML_EDIT"
policy_env_var="COPILOT_PROTECTED_CONFIG_POLICY"

payload="$(cat)"

unique_lines() {
  awk 'NF && !seen[$0]++'
}

is_explicitly_allowed() {
  case "${COPILOT_ALLOW_PYPROJECT_TOML_EDIT:-}" in
    1 | true | TRUE | yes | YES)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

is_read_only_tool() {
  case "$1" in
    ask_user | fetch_copilot_cli_documentation | glob | list_agents | list_bash | read_agent | read_bash | report_intent | rg | sql | task | view | web_fetch)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

ensure_jq() {
  if ! command -v jq >/dev/null 2>&1; then
    echo "protect config hook には jq が必要です" >&2
    exit 1
  fi
}

extract_tool_name() {
  printf '%s' "$payload" | jq -r '.toolName // .tool // empty'
}

extract_tool_args_json() {
  printf '%s' "$payload" | jq -c '
    (.toolArgs // .args // {})
    | if type == "string" then
        (try fromjson catch .)
      else
        .
      end
  '
}

extract_paths_from_patch() {
  local tool_args_json="$1"
  local patch_text

  patch_text="$(printf '%s' "$tool_args_json" | jq -r '
    if type == "string" then
      .
    elif type == "object" then
      .patch // .input // .text // ""
    else
      ""
    end
  ')"

  if [ -z "$patch_text" ]; then
    return 0
  fi

  printf '%s\n' "$patch_text" | sed -n -E \
    -e 's/^\*\*\* (Add|Update|Delete) File: (.+)$/\2/p' \
    -e 's/^\*\*\* Move to: (.+)$/\1/p' | unique_lines
}

extract_target_paths() {
  local tool_name="$1"
  local tool_args_json="$2"

  case "$tool_name" in
    write | edit | create | multiEdit)
      printf '%s' "$tool_args_json" | jq -r '
        [
          .. | objects | (.file_path?, .path?)
        ]
        | map(select(type == "string" and length > 0))
        | unique
        | .[]
      '
      ;;
    apply_patch)
      extract_paths_from_patch "$tool_args_json"
      ;;
    *)
      return 0
      ;;
  esac
}

is_protected_targeted() {
  local tool_name="$1"
  local tool_args_json="$2"
  local target_path

  while IFS= read -r target_path; do
    if [ "$target_path" = "$protected_path" ]; then
      return 0
    fi
  done < <(extract_target_paths "$tool_name" "$tool_args_json")

  return 1
}

normalize_policy() {
  case "${COPILOT_PROTECTED_CONFIG_POLICY:-warn}" in
    block)
      printf 'block'
      ;;
    *)
      printf 'warn'
      ;;
  esac
}

emit_message() {
  local decision="$1"
  local reason

  if [ "$decision" = "deny" ]; then
    reason="pyproject.toml は protected config です。設定ではなくコードを直す方針で対応してください。意図的なメンテナンス変更が必要な場合は Copilot CLI 起動前に ${allow_env_var}=1 を設定してください。"
  else
    reason="pyproject.toml は protected config です。設定ではなくコードを直す方針で対応してください。必要ならこの操作を明示承認してください。恒久的に許可する場合は Copilot CLI 起動前に ${allow_env_var}=1 を設定してください。"
  fi

  cat <<EOF
{"permissionDecision":"${decision}","permissionDecisionReason":"${reason}"}
EOF
}

if is_explicitly_allowed; then
  exit 0
fi

ensure_jq

tool_name="$(extract_tool_name)"
if [ -n "$tool_name" ] && is_read_only_tool "$tool_name"; then
  exit 0
fi

tool_args_json="$(extract_tool_args_json)"
if ! is_protected_targeted "$tool_name" "$tool_args_json"; then
  exit 0
fi

policy="$(normalize_policy)"
if [ "$policy" = "block" ]; then
  emit_message "deny"
  exit 0
fi

emit_message "ask"

exit 0
