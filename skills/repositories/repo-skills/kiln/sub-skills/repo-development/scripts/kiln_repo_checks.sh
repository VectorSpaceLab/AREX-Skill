#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: kiln_repo_checks.sh [--list] [--scope SCOPE] [--run] [--allow-paid]

Print recommended Kiln maintenance commands by default. With --run, execute safe
local scopes. Paid, prerelease, Ollama, and release scopes require --allow-paid
and still assume the user has approved credentials/services/outward-facing steps.

Scopes:
  full          uv run ./checks.sh --agent-mode
  staged        uv run ./checks.sh --staged-only --agent-mode
  python        ruff check, ruff format check, ty check, Python tests
  python-lint   ruff check, ruff format check, ty check
  python-tests  default non-paid Python pytest suite
  server        server and desktop studio pytest subset
  api           server/desktop pytest subset plus OpenAPI schema check
  schema        OpenAPI schema freshness check only
  web           web format, lint, typecheck, tests, and build
  web-fast      web format, lint, and typecheck
  prerelease    curated paid prerelease smoke command (gated)
  paid          full paid pytest command template (gated)
  ollama        Ollama pytest command template (gated)
  release       release digest boundary reminder (print only)
USAGE
}

script_dir() {
  cd "$(dirname "${BASH_SOURCE[0]}")" && pwd
}

find_repo_root() {
  if [[ -n "${KILN_REPO_ROOT:-}" ]]; then
    if [[ -f "$KILN_REPO_ROOT/checks.sh" && -f "$KILN_REPO_ROOT/pyproject.toml" ]]; then
      cd "$KILN_REPO_ROOT" && pwd
      return 0
    fi
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

  local from_script
  from_script="$(script_dir)/../../../../../.."
  if [[ -f "$from_script/checks.sh" && -f "$from_script/pyproject.toml" ]]; then
    cd "$from_script" && pwd
    return 0
  fi

  return 1
}

is_gated_scope() {
  case "$1" in
    prerelease|paid|ollama|release) return 0 ;;
    *) return 1 ;;
  esac
}

commands_for_scope() {
  local scope="$1"
  case "$scope" in
    full)
      printf '%s\n' 'uv run ./checks.sh --agent-mode'
      ;;
    staged)
      printf '%s\n' 'uv run ./checks.sh --staged-only --agent-mode'
      ;;
    python)
      printf '%s\n' \
        'uv run ruff check' \
        'uv run ruff format --check .' \
        'uv run ty check' \
        'uv run python3 -m pytest --benchmark-quiet -q -n auto .'
      ;;
    python-lint)
      printf '%s\n' \
        'uv run ruff check' \
        'uv run ruff format --check .' \
        'uv run ty check'
      ;;
    python-tests)
      printf '%s\n' 'uv run python3 -m pytest --benchmark-quiet -q -n auto .'
      ;;
    server)
      printf '%s\n' 'uv run python3 -m pytest --benchmark-quiet -q libs/server app/desktop/studio_server'
      ;;
    api)
      printf '%s\n' \
        'uv run python3 -m pytest --benchmark-quiet -q libs/server app/desktop/studio_server' \
        'app/web_ui/src/lib/check_schema.sh'
      ;;
    schema)
      printf '%s\n' 'app/web_ui/src/lib/check_schema.sh'
      ;;
    web)
      printf '%s\n' \
        'cd app/web_ui && npm run format_check' \
        'cd app/web_ui && npm run lint' \
        'cd app/web_ui && npm run check' \
        'cd app/web_ui && npm run test_run' \
        'cd app/web_ui && npm run build'
      ;;
    web-fast)
      printf '%s\n' \
        'cd app/web_ui && npm run format_check' \
        'cd app/web_ui && npm run lint' \
        'cd app/web_ui && npm run check'
      ;;
    prerelease)
      printf '%s\n' 'uv run python3 -m pytest --runprerelease -v --tb=short -o "addopts="'
      ;;
    paid)
      printf '%s\n' 'uv run python3 -m pytest --runpaid -v --tb=short -o "addopts=" path/to/test_file.py::test_name'
      ;;
    ollama)
      printf '%s\n' 'uv run python3 -m pytest --ollama -q path/to/test_file.py'
      ;;
    release)
      printf '%s\n' 'Release digest is outward-facing: gather/classify, ask for release name, show message, then post only after confirmation.'
      ;;
    *)
      echo "Unknown scope: $scope" >&2
      return 2
      ;;
  esac
}

list_scopes() {
  usage
}

scope=""
run=false
allow_paid=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --list)
      list_scopes
      exit 0
      ;;
    --scope)
      if [[ $# -lt 2 ]]; then
        echo "--scope requires a value" >&2
        exit 2
      fi
      scope="$2"
      shift 2
      ;;
    --run)
      run=true
      shift
      ;;
    --allow-paid)
      allow_paid=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "$scope" ]]; then
  list_scopes
  exit 0
fi

repo_root="$(find_repo_root)" || {
  echo "Could not locate a Kiln checkout root with checks.sh and pyproject.toml." >&2
  exit 1
}

cd "$repo_root"

echo "Kiln checkout: $repo_root"
echo "Scope: $scope"
echo

mapfile -t commands < <(commands_for_scope "$scope")

if [[ "${#commands[@]}" -eq 0 ]]; then
  echo "No commands for scope: $scope" >&2
  exit 2
fi

if [[ "$run" == false ]]; then
  echo "Recommended command(s):"
  for cmd in "${commands[@]}"; do
    printf '  %s\n' "$cmd"
  done
  if is_gated_scope "$scope"; then
    echo
    echo "This scope is gated. Do not run it without explicit approval, credentials/services, and the relevant human confirmations."
  fi
  exit 0
fi

if is_gated_scope "$scope" && [[ "$allow_paid" == false ]]; then
  echo "Refusing to run gated scope '$scope' without --allow-paid." >&2
  echo "Printing the recommended command(s) instead:" >&2
  for cmd in "${commands[@]}"; do
    printf '  %s\n' "$cmd" >&2
  done
  exit 3
fi

if [[ "$scope" == "release" ]]; then
  echo "Release digest posting cannot be executed by this safety wrapper. Follow the confirmation workflow manually."
  exit 3
fi

for cmd in "${commands[@]}"; do
  echo "+ $cmd"
  bash -lc "$cmd"
done
