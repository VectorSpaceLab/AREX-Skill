#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
find_repo_root() {
  local dir="$SCRIPT_DIR"
  while [[ "$dir" != "/" ]]; do
    if [[ -f "$dir/main.py" && -f "$dir/pyproject.toml" && -d "$dir/src" ]]; then
      printf '%s\n' "$dir"
      return 0
    fi
    dir="$(cd "$dir/.." && pwd)"
  done
  return 1
}
REPO_ROOT="$(find_repo_root)" || { echo "Could not locate the repo root from run_analysis.sh." >&2; exit 1; }

if [[ ${1:-} == "--help" || ${1:-} == "-h" ]]; then
  cat <<'EOF'
Usage: run_analysis.sh [analysis-name|all]

Runs the repo analysis CLI from the repository root.
Examples:
  run_analysis.sh
  run_analysis.sh all
  run_analysis.sh win_rate_by_price
EOF
  exit 0
fi

cd "$REPO_ROOT"
uv run main.py analyze "$@"
