#!/usr/bin/env bash

set -u -o pipefail

STATE_DIR_REL=".github/hooks/state"
STATE_JSON_REL="$STATE_DIR_REL/ruff-quality-gate.json"
SUMMARY_REL="$STATE_DIR_REL/lint-summary.md"

log_debug() {
  if [ -n "${COPILOT_RUFF_GATE_DEBUG_LOG:-}" ]; then
    mkdir -p "$(dirname "$COPILOT_RUFF_GATE_DEBUG_LOG")"
    printf '[ruff_gate_post] %s\n' "$*" >>"$COPILOT_RUFF_GATE_DEBUG_LOG"
  fi
}

unique_lines() {
  awk 'NF && !seen[$0]++'
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

format_markdown_list() {
  local items=("$@")

  if [ "${#items[@]}" -eq 0 ]; then
    printf -- '- none\n'
    return 0
  fi

  for item in "${items[@]}"; do
    printf -- '- %s\n' "$item"
  done
}

if ! command -v jq >/dev/null 2>&1; then
  echo "ruff quality gate には jq が必要です" >&2
  exit 1
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "ruff quality gate には uv が必要です" >&2
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
  echo "ruff quality gate の hook 入力 JSON を解析できませんでした" >&2
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
  echo "ruff quality gate の実行ディレクトリが不正です: $cwd" >&2
  exit 1
fi

mapfile -t changed_python_files < <(
  extract_files_from_tool_args "$tool_name" "$tool_args_json" |
    while IFS= read -r file_path; do
      if [ -n "$file_path" ] && [[ "$file_path" == *.py ]] && [ -f "$cwd/$file_path" ]; then
        printf '%s\n' "$file_path"
      fi
    done | unique_lines
)

if [ "${#changed_python_files[@]}" -eq 0 ]; then
  log_debug "skip reason=no_changed_python_files tool=$tool_name"
  exit 0
fi

state_dir="$cwd/$STATE_DIR_REL"
state_json_path="$cwd/$STATE_JSON_REL"
summary_path="$cwd/$SUMMARY_REL"
mkdir -p "$state_dir"

previous_unresolved_files=()
if [ -f "$state_json_path" ]; then
  mapfile -t previous_unresolved_files < <(
    jq -r '.unresolvedFiles[]?' "$state_json_path" |
      while IFS= read -r file_path; do
        if [ -n "$file_path" ] && [[ "$file_path" == *.py ]] && [ -f "$cwd/$file_path" ]; then
          printf '%s\n' "$file_path"
        fi
      done | unique_lines
  )
fi

mapfile -t candidate_files < <(
  {
    printf '%s\n' "${changed_python_files[@]}"
    printf '%s\n' "${previous_unresolved_files[@]}"
  } | unique_lines
)

if [ "${#candidate_files[@]}" -eq 0 ]; then
  rm -f "$state_json_path" "$summary_path"
  log_debug "clear reason=no_candidates"
  exit 0
fi

format_output=""
if ! format_output="$(
  cd "$cwd" &&
    uv run ruff format --check "${candidate_files[@]}" 2>&1
)"; then
  :
fi

mapfile -t format_fail_files < <(
  printf '%s\n' "$format_output" |
    sed -n -E 's/^Would reformat: (.+)$/\1/p' |
    unique_lines
)

if [ "${#format_fail_files[@]}" -eq 0 ] && [ -n "$format_output" ]; then
  mapfile -t format_fail_files < <(printf '%s\n' "${candidate_files[@]}")
fi

check_output="[]"
if ! check_output="$(
  cd "$cwd" &&
    uv run ruff check --output-format json "${candidate_files[@]}" 2>&1
)"; then
  :
fi

check_output_is_json="0"
if printf '%s' "$check_output" | jq -e . >/dev/null 2>&1; then
  check_output_is_json="1"
fi

check_fail_files=()
check_summary_lines=()
if [ "$check_output_is_json" = "1" ]; then
  mapfile -t check_fail_files < <(
    printf '%s' "$check_output" |
      jq -r '.[].filename' |
      unique_lines
  )
  mapfile -t check_summary_lines < <(
    printf '%s' "$check_output" |
      jq -r '.[] | "- \(.filename):\(.location.row):\(.location.column) [\(.code)] \(.message)"'
  )
elif [ -n "$check_output" ]; then
  mapfile -t check_fail_files < <(printf '%s\n' "${candidate_files[@]}")
fi

mapfile -t unresolved_files < <(
  {
    printf '%s\n' "${format_fail_files[@]}"
    printf '%s\n' "${check_fail_files[@]}"
  } | unique_lines
)

if [ "${#unresolved_files[@]}" -eq 0 ]; then
  rm -f "$state_json_path" "$summary_path"
  log_debug "clear reason=resolved changed=${changed_python_files[*]}"
  exit 0
fi

generated_at="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
unresolved_json="$(printf '%s\n' "${unresolved_files[@]}" | jq -R . | jq -s .)"
changed_json="$(printf '%s\n' "${changed_python_files[@]}" | jq -R . | jq -s .)"

jq -n \
  --arg summaryPath "$SUMMARY_REL" \
  --arg generatedAt "$generated_at" \
  --argjson changedFiles "$changed_json" \
  --argjson unresolvedFiles "$unresolved_json" \
  '{
    summaryPath: $summaryPath,
    generatedAt: $generatedAt,
    changedFiles: $changedFiles,
    unresolvedFiles: $unresolvedFiles
  }' >"$state_json_path"

{
  printf '# Lint summary\n\n'
  printf 'Generated at: %s\n\n' "$generated_at"
  printf 'Changed files:\n'
  format_markdown_list "${changed_python_files[@]}"
  printf '\nUnresolved files:\n'
  format_markdown_list "${unresolved_files[@]}"
  printf '\n## Ruff format --check\n\n'
  if [ -n "$format_output" ]; then
    printf '```\n%s\n```\n' "$format_output"
  else
    printf -- '- none\n'
  fi
  printf '\n## Ruff check\n\n'
  if [ "${#check_summary_lines[@]}" -gt 0 ]; then
    printf '%s\n' "${check_summary_lines[@]}"
  elif [ -n "$check_output" ] && [ "$check_output_is_json" != "1" ]; then
    printf '```\n%s\n```\n' "$check_output"
  else
    printf -- '- none\n'
  fi
} >"$summary_path"

log_debug "updated unresolved=${unresolved_files[*]}"
exit 0
