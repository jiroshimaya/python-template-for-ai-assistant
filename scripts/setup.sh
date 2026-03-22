#!/bin/bash

set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
source "$SCRIPT_DIR/setup_common.sh"

main() {
    echo "🔧 Python AI-assistant Template Setup"
    echo "==================================="
    echo

    check_uv
    setup_python
    setup_precommit

    echo
    echo "✨ Setup complete!"
    echo
    echo "This command is safe to re-run after each clone."
    echo
}

main
