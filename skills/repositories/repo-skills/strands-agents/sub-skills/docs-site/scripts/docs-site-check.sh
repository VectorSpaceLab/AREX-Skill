#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: docs-site-check.sh [--help]

Run the standard docs-site checks from the repository containing the site/
package:
  npm --prefix site run test
  npm --prefix site run typecheck
  npm --prefix site run typecheck:snippets
  npm --prefix site run build
  npm --prefix site run format:check

The script searches upward from the current directory for site/package.json,
then runs each check in order and exits on the first failure.
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi

if [[ $# -gt 0 ]]; then
  echo "Unknown argument: $1" >&2
  usage >&2
  exit 2
fi

find_repo_root() {
  local dir="$PWD"
  while [[ "$dir" != "/" ]]; do
    if [[ -f "$dir/site/package.json" ]]; then
      printf '%s\n' "$dir"
      return 0
    fi
    dir="$(dirname "$dir")"
  done
  return 1
}

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Required command not found: $1" >&2
    exit 1
  fi
}

run_check() {
  local label="$1"
  shift
  echo "==> $label"
  "$@"
}

require_command npm
repo_root="$(find_repo_root)" || {
  echo "Could not find a repository root containing site/package.json" >&2
  exit 1
}
cd "$repo_root"

run_check test npm --prefix site run test
run_check typecheck npm --prefix site run typecheck
run_check snippets npm --prefix site run typecheck:snippets
run_check build npm --prefix site run build
run_check format-check npm --prefix site run format:check
