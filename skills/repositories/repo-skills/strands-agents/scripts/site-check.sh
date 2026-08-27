#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: site-check.sh <mode> [args...]

Run Strands docs-site checks from a repository checkout.

Modes:
  test           npm --prefix site test -- [args...]
  typecheck      npm --prefix site run typecheck
  snippets       npm --prefix site run typecheck:snippets
  build          npm --prefix site run build
  format-check   npm --prefix site run format:check
  help           show this help

The script searches upward for site/package.json. It does not install npm
dependencies and does not regenerate API docs.
EOF
}

find_repo_root() {
  local dir="${PWD}"
  while [[ "$dir" != "/" ]]; do
    if [[ -f "$dir/site/package.json" ]]; then
      printf '%s\n' "$dir"
      return 0
    fi
    dir="$(dirname "$dir")"
  done
  return 1
}

mode="${1:-help}"
if [[ "$mode" == "--help" || "$mode" == "-h" || "$mode" == "help" ]]; then
  usage
  exit 0
fi
shift || true

command -v node >/dev/null || { echo "node is required" >&2; exit 2; }
command -v npm >/dev/null || { echo "npm is required" >&2; exit 2; }
repo_root="$(find_repo_root)" || { echo "could not find Strands site root" >&2; exit 2; }
cd "$repo_root"

case "$mode" in
  test) npm --prefix site test -- "$@" ;;
  typecheck) npm --prefix site run typecheck ;;
  snippets) npm --prefix site run typecheck:snippets ;;
  build) npm --prefix site run build ;;
  format-check) npm --prefix site run format:check ;;
  *) echo "unknown mode: $mode" >&2; usage >&2; exit 2 ;;
esac
