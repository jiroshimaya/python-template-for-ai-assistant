#!/usr/bin/env bash
set -euo pipefail

if gh auth status >/dev/null 2>&1; then
    export COPILOT_HOST_GH_TOKEN
    COPILOT_HOST_GH_TOKEN="$(gh auth token)"

    export COPILOT_HOST_GH_GIT_PROTOCOL
    COPILOT_HOST_GH_GIT_PROTOCOL="$(
        awk '/^[[:space:]]+git_protocol:/{print $2; exit}' "${HOME}/.config/gh/hosts.yml" 2>/dev/null || true
    )"

    if [[ -z "${COPILOT_HOST_GH_GIT_PROTOCOL}" ]]; then
        COPILOT_HOST_GH_GIT_PROTOCOL="https"
    fi
fi

exec docker compose "$@"
