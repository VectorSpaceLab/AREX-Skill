#!/usr/bin/env bash
# Safe selective frontend checker for the PyCaret Control Plane UI.
# Runs npm scripts from apps/web without installing packages or mutating source.

set -u
set -o pipefail

usage() {
  cat <<'EOF'
Usage: ui_static_check.sh [--repo-root PATH] [--typecheck] [--test] [--lint] [--build] [--all] [--help]

Run selected npm verification scripts for the PyCaret React/Vite UI.

Options:
  --repo-root PATH  Repository root containing apps/web (default: auto-detect from cwd)
  --typecheck       Run npm run typecheck
  --test            Run npm test
  --lint            Run npm run lint
  --build           Run npm run build
  --all             Run typecheck, lint, test, and build
  --help            Show this help text

Examples:
  bash scripts/ui_static_check.sh --typecheck --test
  bash scripts/ui_static_check.sh --repo-root REPO_ROOT --all

The script is intentionally non-installing: it expects apps/web/node_modules
or an otherwise usable npm environment to already exist.
EOF
}

msg() { printf '[ui-static-check] %s\n' "$*"; }
err() { printf '[ui-static-check] ERROR: %s\n' "$*" >&2; }

repo_root=""
run_typecheck=0
run_test=0
run_lint=0
run_build=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo-root)
      if [[ $# -lt 2 ]]; then
        err "--repo-root requires a path"
        exit 2
      fi
      repo_root=$2
      shift 2
      ;;
    --typecheck)
      run_typecheck=1
      shift
      ;;
    --test)
      run_test=1
      shift
      ;;
    --lint)
      run_lint=1
      shift
      ;;
    --build)
      run_build=1
      shift
      ;;
    --all)
      run_typecheck=1
      run_test=1
      run_lint=1
      run_build=1
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      err "unknown option: $1"
      usage >&2
      exit 2
      ;;
  esac
done

if [[ $run_typecheck -eq 0 && $run_test -eq 0 && $run_lint -eq 0 && $run_build -eq 0 ]]; then
  err "select at least one check flag or --all"
  usage >&2
  exit 2
fi

find_repo_root() {
  local start=$PWD
  local dir=$start
  while [[ $dir != / ]]; do
    if [[ -f "$dir/apps/web/package.json" ]]; then
      printf '%s\n' "$dir"
      return 0
    fi
    dir=$(dirname "$dir")
  done
  return 1
}

if [[ -z $repo_root ]]; then
  if ! repo_root=$(find_repo_root); then
    err "could not find repository root containing apps/web/package.json; pass --repo-root"
    exit 2
  fi
fi

web_dir="$repo_root/apps/web"
if [[ ! -f "$web_dir/package.json" ]]; then
  err "package.json not found at $web_dir/package.json"
  exit 2
fi

if ! command -v npm >/dev/null 2>&1; then
  err "npm is not on PATH"
  exit 127
fi

msg "repo root: $repo_root"
msg "web dir: $web_dir"
msg "node: $(node --version 2>/dev/null || printf 'not found')"
msg "npm: $(npm --version 2>/dev/null || printf 'not found')"

status=0
run_check() {
  local label=$1
  shift
  msg "running: $label"
  (
    cd "$web_dir" && "$@"
  )
  local code=$?
  if [[ $code -ne 0 ]]; then
    err "$label failed with exit code $code"
    status=$code
  else
    msg "$label passed"
  fi
}

# Keep this order aligned with the common full gate documented in AGENTS.md,
# but allow selective runs for faster iteration.
if [[ $run_typecheck -eq 1 ]]; then
  run_check "npm run typecheck" npm run typecheck
fi
if [[ $run_lint -eq 1 ]]; then
  run_check "npm run lint" npm run lint
fi
if [[ $run_test -eq 1 ]]; then
  run_check "npm test" npm test
fi
if [[ $run_build -eq 1 ]]; then
  run_check "npm run build" npm run build
fi

if [[ $status -ne 0 ]]; then
  err "one or more checks failed"
  exit "$status"
fi

msg "all selected checks passed"
