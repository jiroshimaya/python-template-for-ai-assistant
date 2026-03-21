#!/usr/bin/env bash
set -euo pipefail

development_dir="${DEVELOPMENT_DIR:-${HOME}/development}"

mkdir -p "${HOME}/.config/gh" "${HOME}/.copilot" "${development_dir}"

if ! gh auth status >/dev/null 2>&1 && [[ -n "${COPILOT_HOST_GH_TOKEN:-}" ]]; then
    rm -f "${HOME}/.config/gh/hosts.yml"
    printf '%s' "${COPILOT_HOST_GH_TOKEN}" | gh auth login \
        --hostname github.com \
        --with-token \
        --git-protocol "${COPILOT_HOST_GH_GIT_PROTOCOL:-https}" \
        >/dev/null
fi

exec "$@"
