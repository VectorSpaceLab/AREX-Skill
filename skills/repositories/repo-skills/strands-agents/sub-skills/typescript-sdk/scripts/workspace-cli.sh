#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: workspace-cli.sh <mode> [args...]

Modes:
  help          Show this help
  setup         Install workspace dependencies with npm ci
  dev           Run the strandly workspace CLI
  build         Build the TypeScript workspace
  test          Run the TypeScript workspace tests
  check         Run the TypeScript workspace type-check
  fmt           Format the TypeScript workspace
  fmt-check     Check formatting without writing
  ci            Run the non-install CI sequence
  clean         Remove workspace build artifacts
  rebuild       Clean then build
  package       Run package verification for @strands-agents/sdk
  link          Link strandly on PATH
  bootstrap     setup + link + build + test
  example NAME  Run a standalone example project by name
USAGE
}

find_repo_root() {
  local dir="$PWD"
  while true; do
    if [[ -f "$dir/package.json" && -f "$dir/strands-ts/package.json" && -f "$dir/strandly/package.json" ]]; then
      printf '%s\n' "$dir"
      return 0
    fi
    if [[ "$dir" == "/" ]]; then
      return 1
    fi
    dir=$(dirname "$dir")
  done
}

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    printf 'missing required command: %s\n' "$1" >&2
    exit 1
  fi
}

run() {
  printf '+ %q' "$1"
  shift
  for arg in "$@"; do
    printf ' %q' "$arg"
  done
  printf '\n'
  "$1" "$@"
}

run_in_dir() {
  local dir="$1"
  shift
  printf '+ cd %q && %q' "$dir" "$1"
  shift
  for arg in "$@"; do
    printf ' %q' "$arg"
  done
  printf '\n'
  (cd "$dir" && "$@")
}

require_command node
require_command npm

repo_root=$(find_repo_root) || {
  printf 'could not find a workspace root containing package.json, strands-ts/package.json, and strandly/package.json\n' >&2
  exit 1
}

cd "$repo_root"
mode="${1:-help}"
if [[ "$mode" != "help" ]]; then
  shift || true
fi

case "$mode" in
  setup)
    run npm ci
    ;;
  dev)
    if (($# > 0)); then
      run npm run dev -- "$@"
    else
      run npm run dev
    fi
    ;;
  build)
    run npm run build -w strands-ts
    ;;
  test)
    run npm test -w strands-ts
    ;;
  check)
    run npm run type-check -w strands-ts
    ;;
  fmt)
    run npm run format -w strands-ts
    ;;
  fmt-check)
    run npm run format:check -w strands-ts
    ;;
  ci)
    run npm run format:check -w strands-ts
    run npm run type-check -w strands-ts
    run npm run build -w strands-ts
    run npm test -w strands-ts
    ;;
  clean)
    run npm run clean --workspaces --if-present
    ;;
  rebuild)
    run npm run clean --workspaces --if-present
    run npm run build -w strands-ts
    ;;
  package)
    run npm run test:package -w strands-ts
    ;;
  link)
    run npm link -w strandly
    ;;
  bootstrap)
    run npm ci
    run npm link -w strandly
    run npm run build -w strands-ts
    run npm test -w strands-ts
    ;;
  example)
    if (($# != 1)); then
      printf 'usage: workspace-cli.sh example <name>\n' >&2
      exit 1
    fi
    example_name="$1"
    example_dir="$repo_root/strands-ts/examples/$example_name"
    if [[ ! -d "$example_dir" ]]; then
      printf 'unknown example: %s\n' "$example_name" >&2
      exit 1
    fi
    run_in_dir "$example_dir" npm start
    ;;
  help|-h|--help|'')
    usage
    ;;
  *)
    printf 'unknown mode: %s\n\n' "$mode" >&2
    usage >&2
    exit 1
    ;;
esac
