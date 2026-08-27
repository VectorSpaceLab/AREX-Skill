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
REPO_ROOT="$(find_repo_root)" || { echo "Could not locate the repo root from run_index.sh." >&2; exit 1; }

if [[ ${1:-} == "--help" || ${1:-} == "-h" ]]; then
  cat <<'EOF'
Usage: run_index.sh

Runs the repo indexer CLI from the repository root.
The command opens the interactive indexer menu.
EOF
  exit 0
fi

if [[ $# -gt 0 ]]; then
  echo "run_index.sh does not accept positional arguments." >&2
  exit 2
fi

cd "$REPO_ROOT"
uv run main.py index
