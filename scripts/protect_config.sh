#!/usr/bin/env bash

set -u -o pipefail

protected_path="pyproject.toml"
allow_env_var="COPILOT_ALLOW_PYPROJECT_TOML_EDIT"
policy_env_var="COPILOT_PROTECTED_CONFIG_POLICY"

payload="$(cat)"

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

extract_tool_name() {
  printf '%s' "$payload" | sed -n 's/.*"toolName"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p'
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

case "$payload" in
  *"$protected_path"*)
    ;;
  *)
    exit 0
    ;;
esac

tool_name="$(extract_tool_name)"
if [ -n "$tool_name" ] && is_read_only_tool "$tool_name"; then
  exit 0
fi

policy="$(normalize_policy)"
if [ "$policy" = "block" ]; then
  emit_message "deny"
  exit 0
fi

emit_message "ask"

exit 0
