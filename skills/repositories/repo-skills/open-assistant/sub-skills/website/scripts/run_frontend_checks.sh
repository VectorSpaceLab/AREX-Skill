#!/usr/bin/env bash
# Run selected Open-Assistant website checks from an explicit checkout.
# Examples:
#   bash scripts/run_frontend_checks.sh --repo-root /path/to/Open-Assistant lint typecheck
#   bash scripts/run_frontend_checks.sh --repo-root /path/to/Open-Assistant jest

set -euo pipefail

REPO_ROOT=""
CHECKS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo-root)
      REPO_ROOT="${2:-}"
      shift 2
      ;;
    -h|--help)
      cat <<'EOF'
Usage: run_frontend_checks.sh --repo-root <Open-Assistant checkout> [checks...]

Checks:
  install            npm ci
  lint               npm run lint
  typecheck          npm run typecheck
  jest               npm run jest -- --runInBand
  cypress-contract   npm run cypress:run:contract
  cypress-run        npm run cypress:run
  cypress-component  npm run cypress:component
  storybook-build    npm run build-storybook
  inlang-lint        npm run inlang:lint

If no checks are supplied, runs lint typecheck jest.
EOF
      exit 0
      ;;
    *)
      CHECKS+=("$1")
      shift
      ;;
  esac
done

if [[ -z "$REPO_ROOT" ]]; then
  echo "error: --repo-root is required" >&2
  exit 2
fi

WEBSITE_DIR="$REPO_ROOT/website"
if [[ ! -f "$WEBSITE_DIR/package.json" ]]; then
  echo "error: package.json not found under $WEBSITE_DIR" >&2
  exit 2
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "error: npm is not available on PATH" >&2
  exit 127
fi

if [[ ${#CHECKS[@]} -eq 0 ]]; then
  CHECKS=(lint typecheck jest)
fi

cd "$WEBSITE_DIR"

for check in "${CHECKS[@]}"; do
  case "$check" in
    install)
      npm ci
      ;;
    lint)
      npm run lint
      ;;
    typecheck)
      npm run typecheck
      ;;
    jest)
      npm run jest -- --runInBand
      ;;
    cypress-contract)
      npm run cypress:run:contract
      ;;
    cypress-run)
      npm run cypress:run
      ;;
    cypress-component)
      npm run cypress:component
      ;;
    storybook-build)
      npm run build-storybook
      ;;
    inlang-lint)
      npm run inlang:lint
      ;;
    *)
      echo "error: unknown check '$check'" >&2
      exit 2
      ;;
  esac
done
