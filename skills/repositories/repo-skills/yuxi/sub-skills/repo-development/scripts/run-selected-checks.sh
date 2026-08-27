#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  run-selected-checks.sh [--run] [--with-services] <checks...>

Checks:
  backend-import       Backend package import smoke test.
  cli-pytest           CLI unit test suite.
  frontend-unit        Frontend unit test suite.
  frontend-lint        Frontend ESLint no-write check.
  backend-integration  Backend integration tests.
  backend-e2e          Backend end-to-end tests.
  service-required     Alias for backend-integration and backend-e2e.
  all-safe             backend-import, cli-pytest, frontend-unit, frontend-lint.
  all                  all-safe plus service-required.

Flags:
  --run            Execute the printed commands.
  --with-services  Allow service-required checks. The script never starts or stops
                   Docker Compose services for you.

Notes:
  - Run this helper inside a Yuxi git checkout.
  - Without --run, the helper only prints the commands.
  - Service-required checks are skipped unless --with-services is present.
EOF
}

ROOT_DIR="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "$ROOT_DIR" ]]; then
  echo "error: run this helper inside a Yuxi git checkout"
  exit 1
fi

RUN=false
WITH_SERVICES=false
declare -a REQUESTS=()

while (($# > 0)); do
  case "$1" in
    --run)
      RUN=true
      ;;
    --with-services)
      WITH_SERVICES=true
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    backend-import|cli-pytest|frontend-unit|frontend-lint|backend-integration|backend-e2e|service-required|all-safe|all)
      REQUESTS+=("$1")
      ;;
    *)
      echo "error: unknown argument: $1"
      usage
      exit 1
      ;;
  esac
  shift
done

if ((${#REQUESTS[@]} == 0)); then
  usage
  exit 1
fi

BLOCKED_SERVICE_CHECKS=false

print_step() {
  local label="$1"
  local cwd="$2"
  shift 2
  local -a cmd=("$@")

  printf '\n[%s]\n' "$label"
  printf '  cwd: %s\n' "$cwd"
  printf '  cmd: '
  if [[ "$cwd" != "." ]]; then
    printf 'cd %s && ' "$cwd"
  fi
  printf '%q ' "${cmd[@]}"
  printf '\n'
}

run_step() {
  local label="$1"
  local cwd="$2"
  shift 2
  local -a cmd=("$@")

  print_step "$label" "$cwd" "${cmd[@]}"
  if $RUN; then
    if [[ "$cwd" == "." ]]; then
      (cd "$ROOT_DIR" && "${cmd[@]}")
    else
      (cd "$ROOT_DIR/$cwd" && "${cmd[@]}")
    fi
  fi
}

run_backend_import() {
  run_step "backend-import" "backend" uv run --group test pytest test/unit/test_package_import.py
}

run_cli_pytest() {
  run_step "cli-pytest" "packages/yuxi-cli" uv run --group test pytest
}

run_frontend_unit() {
  run_step "frontend-unit" "web" pnpm test:unit
}

run_frontend_lint() {
  run_step "frontend-lint" "web" pnpm exec eslint . --cache --max-warnings 0
}

run_backend_integration() {
  if [[ "$WITH_SERVICES" != true ]]; then
    print_step "backend-integration" "." docker compose exec api uv run --group test pytest test/integration
    printf '  note: service-required; start Docker Compose yourself, then rerun with --with-services.\n'
    BLOCKED_SERVICE_CHECKS=true
    return 0
  fi

  run_step "backend-integration" "." docker compose exec api uv run --group test pytest test/integration
}

run_backend_e2e() {
  if [[ "$WITH_SERVICES" != true ]]; then
    print_step "backend-e2e" "." docker compose exec api uv run --group test pytest test/e2e -m e2e
    printf '  note: service-required; start Docker Compose yourself, then rerun with --with-services.\n'
    BLOCKED_SERVICE_CHECKS=true
    return 0
  fi

  run_step "backend-e2e" "." docker compose exec api uv run --group test pytest test/e2e -m e2e
}

run_all_safe() {
  run_backend_import
  run_cli_pytest
  run_frontend_unit
  run_frontend_lint
}

for request in "${REQUESTS[@]}"; do
  case "$request" in
    backend-import)
      run_backend_import
      ;;
    cli-pytest)
      run_cli_pytest
      ;;
    frontend-unit)
      run_frontend_unit
      ;;
    frontend-lint)
      run_frontend_lint
      ;;
    backend-integration)
      run_backend_integration
      ;;
    backend-e2e)
      run_backend_e2e
      ;;
    service-required)
      run_backend_integration
      run_backend_e2e
      ;;
    all-safe)
      run_all_safe
      ;;
    all)
      run_all_safe
      run_backend_integration
      run_backend_e2e
      ;;
  esac
done

if $RUN && $BLOCKED_SERVICE_CHECKS; then
  exit 2
fi
