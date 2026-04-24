#!/bin/bash

set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
source "$SCRIPT_DIR/setup_common.sh"

main() {
    echo "🚀 Python AI-assistant Template Init"
    echo "=================================="
    echo

    check_git_version
    check_uv
    check_github_cli
    get_project_name
    echo

    update_project_name
    setup_python
    setup_git_hooks

    echo
    echo "✨ Init complete!"
    echo
    echo "Next steps:"
    echo "1. Update the README.md with your project description"
    echo "2. Update author information in pyproject.toml"
    echo "3. Set up branch protection (optional):"
    echo "   gh repo view --web  # Open in browser to configure"
    echo "4. Use sh scripts/setup.sh after each clone or worktree creation"
    echo
}

main
