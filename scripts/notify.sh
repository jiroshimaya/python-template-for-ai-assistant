#!/usr/bin/env bash

set -u -o pipefail

log_debug() {
  echo "[notify_hook] $*" >&2
  if [ -n "${COPILOT_NTFY_DEBUG_LOG:-}" ]; then
    mkdir -p "$(dirname "$COPILOT_NTFY_DEBUG_LOG")"
    printf '[notify_hook] %s\n' "$*" >>"$COPILOT_NTFY_DEBUG_LOG"
  fi
}

topic="${COPILOT_NTFY_TOPIC:-}"
if [ -z "$topic" ]; then
  log_debug "skip reason=no_topic"
  exit 0
fi

if ! command -v jq >/dev/null 2>&1; then
  log_debug "skip reason=missing_jq"
  echo "jq が見つからないため ntfy.sh 通知をスキップします" >&2
  exit 0
fi

if ! command -v curl >/dev/null 2>&1; then
  log_debug "skip reason=missing_curl"
  echo "curl が見つからないため ntfy.sh 通知をスキップします" >&2
  exit 0
fi

input="$(cat)"
server="${COPILOT_NTFY_SERVER:-https://ntfy.sh}"
priority="${COPILOT_NTFY_PRIORITY:-default}"
configured_event_name="${COPILOT_HOOK_EVENT:-}"

if ! cwd="$(printf '%s' "$input" | jq -r '.cwd // ""')" ||
  ! formatted_timestamp="$(printf '%s' "$input" | jq -r 'if .timestamp == null then empty else ((.timestamp / 1000) + (9 * 60 * 60) | floor | strftime("%Y/%m/%d %H:%M:%S")) end')" ||
  ! tool_name="$(printf '%s' "$input" | jq -r '.toolName // .tool // empty')" ||
  ! tool_args="$(printf '%s' "$input" | jq -r '.toolArgs // empty')" ||
  ! stop_reason="$(printf '%s' "$input" | jq -r '.reason // .stopReason // empty')" ||
  ! fallback_tool_args="$(printf '%s' "$input" | jq -r '(.args // []) | join(" ")')"; then
  log_debug "skip reason=invalid_json"
  echo "hook 入力の JSON 解析に失敗したため通知をスキップします" >&2
  exit 0
fi

if [ -z "$tool_args" ]; then
  tool_args="$fallback_tool_args"
fi

event_name="$configured_event_name"
if [ -z "$event_name" ]; then
  if [ -n "$tool_name" ]; then
    event_name="preToolUse"
  else
    event_name="agentStop"
  fi
fi

build_pre_tool_use_message() {
  local tool_name="$1"
  local tool_args="$2"
  local question
  local choices_str

  if [ "$tool_name" != "ask_user" ]; then
    log_debug "skip reason=not_ask_user tool=$tool_name"
    return 1
  fi

  title="${COPILOT_NTFY_TITLE:-Copilot CLI: ユーザ確認待ち}"
  question="$(printf '%s' "$tool_args" | jq -r '.question // empty' 2>/dev/null || true)"
  choices_str="$(printf '%s' "$tool_args" | jq -r '(.choices // []) | join(", ")' 2>/dev/null || true)"
  message=""

  if [ -n "$question" ]; then
    message="question: $question"
  fi
  if [ -n "$choices_str" ]; then
    message="$message
choices: $choices_str"
  fi
  if [ -z "$message" ] && [ -n "$tool_args" ]; then
    message="args: $tool_args"
  fi
}

build_agent_stop_message() {
  local stop_reason="$1"

  title="${COPILOT_NTFY_TITLE:-Copilot CLI: エージェント停止}"
  message=""

  if [ -n "$stop_reason" ]; then
    message="reason: $stop_reason"
  fi
}

case "$event_name" in
  preToolUse)
    if ! build_pre_tool_use_message "$tool_name" "$tool_args"; then
      exit 0
    fi
    ;;
  agentStop)
    build_agent_stop_message "$stop_reason"
    ;;
  *)
    log_debug "skip reason=unsupported_event event=$event_name"
    exit 0
    ;;
esac

message="$message
cwd: $cwd"

if [ -n "$formatted_timestamp" ]; then
  message="$message
timestamp: $formatted_timestamp"
fi

log_debug "event=$event_name topic=$topic cwd=$cwd"

if ! curl \
  --silent \
  --show-error \
  --fail \
  -X POST \
  -H "Title: $title" \
  -H "Priority: $priority" \
  --data-binary "$message" \
  "${server%/}/$topic" >/dev/null; then
  log_debug "send=failed event=$event_name topic=$topic"
  echo "ntfy.sh への通知に失敗しました" >&2
else
  log_debug "send=ok event=$event_name topic=$topic"
fi

exit 0
