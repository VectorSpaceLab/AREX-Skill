#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: ts-core-check.sh <mode> [args...]

Modes:
  check         Run lint, format-check, type-check, and browser bundle checks
  test          Run the TypeScript workspace unit tests
  build         Build the TypeScript workspace
  package       Run package verification for @strands-agents/sdk
  coverage      Run workspace coverage tests
  browser       Run browser unit tests
  browser-note  Print the browser-install reminder without mutating anything
  full-check    Run the maintained package check script (may format files)
  help          Show this help
USAGE
}

find_repo_root() {
  local dir="$PWD"
  while true; do
    if [[ -f "$dir/package.json" && -f "$dir/strands-ts/package.json" ]]; then
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

require_command node
require_command npm

node_major=$(node -p 'Number(process.versions.node.split(".")[0])')
if (( node_major < 20 )); then
  printf 'node>=20 is required, found %s\n' "$(node -v)" >&2
  exit 1
fi

repo_root=$(find_repo_root) || {
  printf 'could not find a workspace root containing package.json and strands-ts/package.json\n' >&2
  exit 1
}

cd "$repo_root"

mode="${1:-help}"
if [[ "$mode" != "help" ]]; then
  shift || true
fi

run() {
  printf '+ %q' "$1"
  shift
  for arg in "$@"; do
    printf ' %q' "$arg"
  done
  printf '\n'
  "$1" "$@"
}

case "$mode" in
  check)
    run npm run lint -w strands-ts
    run npm run format:check -w strands-ts
    run npm run type-check -w strands-ts
    run npm run check:browser-bundle -w strands-ts
    ;;
  test)
    if (($# > 0)); then
      run npm test -w strands-ts -- "$@"
    else
      run npm test -w strands-ts
    fi
    ;;
  build)
    run npm run build -w strands-ts
    ;;
  package)
    run npm run test:package -w strands-ts
    ;;
  coverage)
    run npm run test:coverage -w strands-ts
    ;;
  browser)
    if (($# > 0)); then
      run npm run test:browser -w strands-ts -- "$@"
    else
      run npm run test:browser -w strands-ts
    fi
    ;;
  browser-note)
    cat <<'NOTE'
Browser tests are separate from Node tests.

If Chromium or Playwright is missing, install the browser runtime before running
browser-only checks. Keep browser bundle validation and browser execution as
separate steps.

Useful commands:
- npm run test:browser:install -w strands-ts
- npm run test:browser -w strands-ts
- npm run check:browser-bundle -w strands-ts
NOTE
    ;;
  full-check)
    run npm run check -w strands-ts
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
