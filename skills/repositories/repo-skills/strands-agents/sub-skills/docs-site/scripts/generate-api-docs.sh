#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: generate-api-docs.sh [--all | --python | --typescript | --help]

Regenerate docs-site API reference output through the documented site npm
scripts when they are present in site/package.json.

Options:
  --all          Run the combined API generation command if available, otherwise
                 run the Python and TypeScript generation commands in order.
                 This is the default.
  --python       Run npm --prefix site run sdk:generate:py.
  --typescript   Run npm --prefix site run sdk:generate:ts.
  --help         Show this help.

Generated API docs are build output. Review the generated diff after this
script runs; do not hand-edit files under generated API output.
EOF
}

mode="all"
case "${1:-}" in
  ""|--all)
    mode="all"
    ;;
  --python)
    mode="python"
    ;;
  --typescript)
    mode="typescript"
    ;;
  --help|-h)
    usage
    exit 0
    ;;
  *)
    echo "Unknown argument: $1" >&2
    usage >&2
    exit 2
    ;;
esac

if [[ $# -gt 1 ]]; then
  echo "Too many arguments" >&2
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

has_npm_script() {
  local name="$1"
  node -e '
    const fs = require("fs");
    const name = process.argv[1];
    const pkg = JSON.parse(fs.readFileSync("site/package.json", "utf8"));
    process.exit(pkg.scripts && pkg.scripts[name] ? 0 : 1);
  ' "$name"
}

run_npm_script() {
  local name="$1"
  if ! has_npm_script "$name"; then
    echo "Missing npm script in site/package.json: $name" >&2
    exit 1
  fi
  echo "==> npm --prefix site run $name"
  npm --prefix site run "$name"
}

require_command npm
require_command node
repo_root="$(find_repo_root)" || {
  echo "Could not find a repository root containing site/package.json" >&2
  exit 1
}
cd "$repo_root"

case "$mode" in
  all)
    if has_npm_script "sdk:generate"; then
      run_npm_script "sdk:generate"
    else
      run_npm_script "sdk:generate:py"
      run_npm_script "sdk:generate:ts"
    fi
    ;;
  python)
    run_npm_script "sdk:generate:py"
    ;;
  typescript)
    run_npm_script "sdk:generate:ts"
    ;;
esac

echo "==> API generation complete. Review generated API docs and run docs-site checks."
