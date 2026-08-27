#!/usr/bin/env bash
set -euo pipefail

# Build a wheel for a SecretFlow plugin project.
#
# Usage:
#   ./build_plugin_wheel.sh [plugin-directory]
#
# If no directory is provided, the script uses the current directory.
# It only builds the wheel and prints the produced file path.

plugin_dir="${1:-.}"
cd "$plugin_dir"

python -m build --wheel

echo "Built wheel(s) in: $(pwd)/dist"
ls -1 dist/*.whl
