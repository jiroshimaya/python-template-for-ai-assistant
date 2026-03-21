#!/usr/bin/env bash

set -u -o pipefail

log_debug() {
  if [ -n "${COPILOT_RUFF_HOOK_DEBUG_LOG:-}" ]; then
    mkdir -p "$(dirname "$COPILOT_RUFF_HOOK_DEBUG_LOG")"
    printf '[ruff_hook] %s\n' "$*" >>"$COPILOT_RUFF_HOOK_DEBUG_LOG"
  fi
}

print_failure() {
  local failed_command="$1"
  local command_output="$2"
  shift 2
  local files=("$@")

  printf 'postToolUse ruff 失敗\n'
  printf '対象ファイル: %s\n' "$(IFS=', '; echo "${files[*]}")"
  printf '失敗コマンド: %s\n' "$failed_command"
  printf '出力:\n%s\n' "$command_output"
  printf '次アクション:\n'
  printf -- '- 上記の指摘を修正してください\n'
  printf -- '- 必要なら `%s` を再実行してください\n' "$failed_command"
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
        -e 's/^\*\*\* Move to: (.+)$/\1/p' | awk '!seen[$0]++'
      ;;
    *)
      return 0
      ;;
  esac
}

is_target_tool() {
  case "$1" in
    write | edit | create | multiEdit | apply_patch)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

if ! command -v jq >/dev/null 2>&1; then
  echo "postToolUse ruff hook の実行に jq が必要です"
  exit 1
fi

input="$(cat)"

if ! cwd="$(printf '%s' "$input" | jq -r '.cwd // empty')" ||
  ! tool_name="$(printf '%s' "$input" | jq -r '.toolName // .tool // empty')" ||
  ! tool_result_type="$(printf '%s' "$input" | jq -r '
    .toolResult.resultType //
    (if (.exitCode // 0) == 0 then "success" else "failure" end)
  ')" ||
  ! tool_args_json="$(printf '%s' "$input" | jq -c '
    (.toolArgs // .args // {})
    | if type == "string" then
        (try fromjson catch .)
      else
        .
      end
  ')"; then
  echo "postToolUse ruff hook の入力 JSON を解析できませんでした"
  exit 1
fi

if [ -z "$tool_name" ] || ! is_target_tool "$tool_name"; then
  log_debug "skip reason=non_target_tool tool=${tool_name:-}"
  exit 0
fi

if [ "$tool_result_type" != "success" ]; then
  log_debug "skip reason=tool_failed tool=$tool_name result_type=$tool_result_type"
  exit 0
fi

if [ -z "$cwd" ] || [ ! -d "$cwd" ]; then
  echo "postToolUse ruff hook の実行ディレクトリが不正です: $cwd"
  exit 1
fi

mapfile -t candidate_files < <(extract_files_from_tool_args "$tool_name" "$tool_args_json")

python_files=()
for file_path in "${candidate_files[@]}"; do
  if [ -n "$file_path" ] && [[ "$file_path" == *.py ]]; then
    python_files+=("$file_path")
  fi
done

if [ "${#python_files[@]}" -eq 0 ]; then
  log_debug "skip reason=no_python_files tool=$tool_name"
  exit 0
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "postToolUse ruff hook の実行に uv が必要です"
  exit 1
fi

format_command=(uv run ruff format "${python_files[@]}")
check_command=(uv run ruff check "${python_files[@]}")

format_output=""
if ! format_output="$(
  cd "$cwd" &&
    "${format_command[@]}" 2>&1
)"; then
  print_failure "${format_command[*]}" "$format_output" "${python_files[@]}"
  exit 2
fi

check_output=""
if ! check_output="$(
  cd "$cwd" &&
    "${check_command[@]}" 2>&1
)"; then
  print_failure "${check_command[*]}" "$check_output" "${python_files[@]}"
  exit 2
fi

printf 'postToolUse ruff 成功\n'
printf '対象ファイル: %s\n' "$(IFS=', '; echo "${python_files[*]}")"
printf '実行コマンド:\n'
printf -- '- %s\n' "${format_command[*]}"
printf -- '- %s\n' "${check_command[*]}"

exit 0
