#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: kiln_repo_checks.sh [--list] [--scope SCOPE] [--repo-root PATH] [--run]

Print targeted Kiln checkout validation commands. With --run, execute only safe
local scopes. This helper never runs paid/prerelease/Ollama/cloud/release scopes.

Scopes:
  full          uv run ./checks.sh --agent-mode
  staged        uv run ./checks.sh --staged-only --agent-mode
  python-lint   uv run ruff check; uv run ruff format --check .; uv run ty check
  python-tests  uv run python3 -m pytest --benchmark-quiet -q -n auto .
  server        uv run python3 -m pytest --benchmark-quiet -q libs/server app/desktop/studio_server
  schema        app/web_ui/src/lib/check_schema.sh
  web-fast      npm format/lint/check from app/web_ui
  web           npm format/lint/check/test/build from app/web_ui
USAGE
}

scope=""
run=false
repo_root="${KILN_REPO_ROOT:-}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --list|-h|--help)
      usage
      exit 0
      ;;
    --scope)
      [[ $# -ge 2 ]] || { echo "--scope requires a value" >&2; exit 2; }
      scope="$2"
      shift 2
      ;;
    --repo-root)
      [[ $# -ge 2 ]] || { echo "--repo-root requires a value" >&2; exit 2; }
      repo_root="$2"
      shift 2
      ;;
    --run)
      run=true
      shift
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

find_repo_root() {
  if [[ -n "$repo_root" && -f "$repo_root/checks.sh" && -f "$repo_root/pyproject.toml" ]]; then
    cd "$repo_root" && pwd
    return 0
  fi
  local dir
  dir="$(pwd)"
  while [[ "$dir" != "/" ]]; do
    if [[ -f "$dir/checks.sh" && -f "$dir/pyproject.toml" ]]; then
      echo "$dir"
      return 0
    fi
    dir="$(dirname "$dir")"
  done
  return 1
}

commands_for_scope() {
  case "$1" in
    full) printf '%s\n' 'uv run ./checks.sh --agent-mode' ;;
    staged) printf '%s\n' 'uv run ./checks.sh --staged-only --agent-mode' ;;
    python-lint) printf '%s\n' 'uv run ruff check' 'uv run ruff format --check .' 'uv run ty check' ;;
    python-tests) printf '%s\n' 'uv run python3 -m pytest --benchmark-quiet -q -n auto .' ;;
    server) printf '%s\n' 'uv run python3 -m pytest --benchmark-quiet -q libs/server app/desktop/studio_server' ;;
    schema) printf '%s\n' 'app/web_ui/src/lib/check_schema.sh' ;;
    web-fast) printf '%s\n' 'cd app/web_ui && npm run format_check' 'cd app/web_ui && npm run lint' 'cd app/web_ui && npm run check' ;;
    web) printf '%s\n' 'cd app/web_ui && npm run format_check' 'cd app/web_ui && npm run lint' 'cd app/web_ui && npm run check' 'cd app/web_ui && npm run test_run' 'cd app/web_ui && npm run build' ;;
    *) echo "Unknown scope: $1" >&2; return 2 ;;
  esac
}

if [[ -z "$scope" ]]; then
  usage
  exit 0
fi

root="$(find_repo_root)" || { echo "Could not locate a Kiln checkout root; pass --repo-root." >&2; exit 1; }
cd "$root"
mapfile -t commands < <(commands_for_scope "$scope")

echo "Kiln checkout: $root"
echo "Scope: $scope"
if [[ "$run" == false ]]; then
  echo "Recommended command(s):"
  for cmd in "${commands[@]}"; do printf '  %s\n' "$cmd"; done
  exit 0
fi

for cmd in "${commands[@]}"; do
  echo "+ $cmd"
  bash -lc "$cmd"
done
