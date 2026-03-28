#!/usr/bin/env bash

MAIN_SYNC_STATE_DIR_REL=".github/hooks/state"
MAIN_SYNC_STATE_JSON_REL="$MAIN_SYNC_STATE_DIR_REL/main-status.json"
MAIN_SYNC_BASE_REF="origin/main"

ensure_main_sync_jq() {
  if ! command -v jq >/dev/null 2>&1; then
    echo "main sync guard には jq が必要です" >&2
    exit 1
  fi
}

main_sync_fetch_origin_main() {
  git fetch origin main --quiet
}

main_sync_head_sha() {
  git rev-parse HEAD
}

main_sync_origin_main_sha() {
  git rev-parse "$MAIN_SYNC_BASE_REF"
}

main_sync_merge_base_sha() {
  git merge-base HEAD "$MAIN_SYNC_BASE_REF"
}

main_sync_status_from_commits() {
  local head_sha="$1"
  local origin_main_sha="$2"
  local merge_base_sha="$3"

  if [ "$head_sha" = "$origin_main_sha" ]; then
    printf 'up_to_date'
  elif [ "$merge_base_sha" = "$head_sha" ]; then
    printf 'behind_main'
  elif [ "$merge_base_sha" = "$origin_main_sha" ]; then
    printf 'ahead_of_main'
  else
    printf 'diverged'
  fi
}

write_main_sync_state() {
  local cwd="$1"
  local status="$2"
  local head_sha="$3"
  local origin_main_sha="$4"
  local merge_base_sha="$5"
  local state_dir="$cwd/$MAIN_SYNC_STATE_DIR_REL"
  local state_json_path="$cwd/$MAIN_SYNC_STATE_JSON_REL"
  local generated_at

  generated_at="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  mkdir -p "$state_dir"

  jq -n \
    --arg baseRef "$MAIN_SYNC_BASE_REF" \
    --arg generatedAt "$generated_at" \
    --arg status "$status" \
    --arg headSha "$head_sha" \
    --arg originMainSha "$origin_main_sha" \
    --arg mergeBaseSha "$merge_base_sha" \
    '{
      baseRef: $baseRef,
      generatedAt: $generatedAt,
      status: $status,
      headSha: $headSha,
      originMainSha: $originMainSha,
      mergeBaseSha: $mergeBaseSha
    }' >"$state_json_path"
}

read_main_sync_status() {
  local state_json_path="$1"

  jq -r '.status // empty' "$state_json_path"
}

read_main_sync_snapshot() {
  local state_json_path="$1"

  jq -r '[.status // "", .headSha // "", .originMainSha // "", .mergeBaseSha // ""] | @tsv' "$state_json_path"
}

refresh_main_sync_state_from_local_refs() {
  local cwd="$1"
  local state_json_path="$2"
  local stored_status stored_head_sha stored_origin_main_sha stored_merge_base_sha
  local current_head_sha current_origin_main_sha current_merge_base_sha current_status

  IFS=$'\t' read -r \
    stored_status \
    stored_head_sha \
    stored_origin_main_sha \
    stored_merge_base_sha < <(read_main_sync_snapshot "$state_json_path")

  if ! current_head_sha="$(main_sync_head_sha 2>/dev/null)"; then
    printf '%s' "$stored_status"
    return 0
  fi

  if ! current_origin_main_sha="$(main_sync_origin_main_sha 2>/dev/null)"; then
    printf '%s' "$stored_status"
    return 0
  fi

  if ! current_merge_base_sha="$(main_sync_merge_base_sha 2>/dev/null)"; then
    printf '%s' "$stored_status"
    return 0
  fi

  current_status="$(
    main_sync_status_from_commits \
      "$current_head_sha" \
      "$current_origin_main_sha" \
      "$current_merge_base_sha"
  )"

  if [ "$stored_status" != "$current_status" ] ||
    [ "$stored_head_sha" != "$current_head_sha" ] ||
    [ "$stored_origin_main_sha" != "$current_origin_main_sha" ] ||
    [ "$stored_merge_base_sha" != "$current_merge_base_sha" ]; then
    write_main_sync_state \
      "$cwd" \
      "$current_status" \
      "$current_head_sha" \
      "$current_origin_main_sha" \
      "$current_merge_base_sha"
  fi

  printf '%s' "$current_status"
}

is_main_sync_blocked_status() {
  case "$1" in
    behind_main | diverged)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

is_main_sync_mutating_tool() {
  case "$1" in
    apply_patch | bash | create | edit | multiEdit | stop_bash | task | write | write_bash)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

trim_main_sync_shell_text() {
  local value="$1"

  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"
  printf '%s' "$value"
}

is_main_sync_safe_shell_segment() {
  local segment

  segment="$(trim_main_sync_shell_text "$1")"
  if [ -z "$segment" ]; then
    return 0
  fi

  case "$segment" in
    *'|'* | *';'* | *'>'* | *'<'* | *'`'* | *'$('* | *'${'*)
      return 1
      ;;
  esac

  case "$segment" in
    git\ fetch* | git\ status* | git\ branch* | git\ log* | git\ diff* | git\ rev-parse* | git\ merge-base*)
      return 0
      ;;
    git\ pull*)
      return 0
      ;;
    git\ rebase\ *origin/main* | git\ merge\ *origin/main*)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

is_main_sync_allowed_shell_command() {
  local command="$1"
  local remaining segment without_double_and

  command="$(trim_main_sync_shell_text "$command")"
  if [ -z "$command" ]; then
    return 1
  fi

  case "$command" in
    *$'\n'* | *'||'*)
      return 1
      ;;
  esac

  without_double_and="${command//&&/}"
  case "$without_double_and" in
    *'&'*)
      return 1
      ;;
  esac

  remaining="$command"
  while :; do
    if [[ "$remaining" == *"&&"* ]]; then
      segment="${remaining%%&&*}"
      remaining="${remaining#*&&}"
    else
      segment="$remaining"
      remaining=""
    fi

    if ! is_main_sync_safe_shell_segment "$segment"; then
      return 1
    fi

    if [ -z "$remaining" ]; then
      return 0
    fi
  done
}

main_sync_resolution_message() {
  case "$1" in
    behind_main)
      printf 'Your branch is behind origin/main. Run git rebase origin/main or git merge origin/main before continuing.'
      ;;
    diverged)
      printf 'Your branch has diverged from origin/main. Run git rebase origin/main or git merge origin/main before continuing.'
      ;;
    *)
      echo "unsupported main sync status: $1" >&2
      return 1
      ;;
  esac
}
