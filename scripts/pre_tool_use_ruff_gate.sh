#!/usr/bin/env bash

set -u -o pipefail

STATE_JSON_REL=".github/hooks/state/ruff-quality-gate.json"
SUMMARY_REL=".github/hooks/state/lint-summary.md"

log_debug() {
  if [ -n "${COPILOT_RUFF_GATE_DEBUG_LOG:-}" ]; then
    mkdir -p "$(dirname "$COPILOT_RUFF_GATE_DEBUG_LOG")"
    printf '[ruff_gate_pre] %s\n' "$*" >>"$COPILOT_RUFF_GATE_DEBUG_LOG"
  fi
}

unique_lines() {
  awk 'NF && !seen[$0]++'
}

extract_files_from_tool_args() {
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
      ;;
    *)
      return 0
      ;;
  esac
}

path_in_list() {
  local target="$1"
  shift
  local item

  for item in "$@"; do
    if [ "$item" = "$target" ]; then
      return 0
    fi
  done

  return 1
}

deny_with_reason() {
  local summary_path="$1"
  shift
  local unresolved_files=("$@")
  local file_list

  file_list="$(IFS=', '; echo "${unresolved_files[*]}")"
  jq -cn \
    --arg reason "Lint warnings remain. Read ${summary_path} and fix the affected files first: ${file_list}" \
    '{
      permissionDecision: "deny",
      permissionDecisionReason: $reason
    }'
}

if ! command -v jq >/dev/null 2>&1; then
  echo "ruff quality gate には jq が必要です" >&2
  exit 1
fi

input="$(cat)"

if ! cwd="$(printf '%s' "$input" | jq -r '.cwd // empty')" ||
  ! tool_name="$(printf '%s' "$input" | jq -r '.toolName // .tool // empty')" ||
  ! tool_args_json="$(printf '%s' "$input" | jq -c '
    (.toolArgs // .args // {})
    | if type == "string" then
        (try fromjson catch .)
      else
        .
      end
  ')"; then
  echo "ruff quality gate の hook 入力 JSON を解析できませんでした" >&2
  exit 1
fi

if [ -z "$cwd" ] || [ ! -d "$cwd" ]; then
  echo "ruff quality gate の実行ディレクトリが不正です: $cwd" >&2
  exit 1
fi

state_json_path="$cwd/$STATE_JSON_REL"
if [ ! -f "$state_json_path" ]; then
  exit 0
fi

mapfile -t unresolved_files < <(jq -r '.unresolvedFiles[]?' "$state_json_path" | unique_lines)
if [ "${#unresolved_files[@]}" -eq 0 ]; then
  exit 0
fi

case "$tool_name" in
  ask_user | view | rg | glob)
    log_debug "allow reason=read_only tool=$tool_name"
    exit 0
    ;;
esac

case "$tool_name" in
  write | edit | multiEdit | apply_patch)
    mapfile -t target_files < <(
      extract_files_from_tool_args "$tool_name" "$tool_args_json" |
        while IFS= read -r file_path; do
          if [ -n "$file_path" ] && [[ "$file_path" == *.py ]]; then
            printf '%s\n' "$file_path"
          fi
        done | unique_lines
    )

    if [ "${#target_files[@]}" -eq 0 ]; then
      deny_with_reason "$SUMMARY_REL" "${unresolved_files[@]}"
      exit 0
    fi

    for target_file in "${target_files[@]}"; do
      if ! path_in_list "$target_file" "${unresolved_files[@]}"; then
        deny_with_reason "$SUMMARY_REL" "${unresolved_files[@]}"
        exit 0
      fi
    done

    log_debug "allow reason=fixing_unresolved tool=$tool_name files=${target_files[*]}"
    exit 0
    ;;
esac

deny_with_reason "$SUMMARY_REL" "${unresolved_files[@]}"
exit 0
