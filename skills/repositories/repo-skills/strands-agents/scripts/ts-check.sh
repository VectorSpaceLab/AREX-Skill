#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: ts-check.sh <mode> [args...]

Run Strands TypeScript workspace checks from a repository checkout.

Modes:
  check            npm run check -w strands-ts
  type-check       npm run type-check -w strands-ts
  lint             npm run lint -w strands-ts
  format-check     npm run format:check -w strands-ts
  test             npm test -w strands-ts -- [args...]
  build            npm run build -w strands-ts
  package          npm run test:package -w strands-ts
  browser-bundle   npm run check:browser-bundle -w strands-ts
  help             show this help

The script searches upward for a checkout containing package.json and
strands-ts/package.json. It does not install npm dependencies.
EOF
}

find_repo_root() {
  local dir="${PWD}"
  while [[ "$dir" != "/" ]]; do
    if [[ -f "$dir/package.json" && -f "$dir/strands-ts/package.json" ]]; then
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
repo_root="$(find_repo_root)" || { echo "could not find Strands workspace root" >&2; exit 2; }
cd "$repo_root"

case "$mode" in
  check) npm run check -w strands-ts ;;
  type-check) npm run type-check -w strands-ts ;;
  lint) npm run lint -w strands-ts ;;
  format-check) npm run format:check -w strands-ts ;;
  test) npm test -w strands-ts -- "$@" ;;
  build) npm run build -w strands-ts ;;
  package) npm run test:package -w strands-ts ;;
  browser-bundle) npm run check:browser-bundle -w strands-ts ;;
  *) echo "unknown mode: $mode" >&2; usage >&2; exit 2 ;;
esac
