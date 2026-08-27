#!/usr/bin/env bash
# Help-only smoke checks for the Browser Use persistent CLI.
# This script avoids browser launch, cloud provisioning, profile sync, tunnels,
# and credential use unless the caller explicitly adds --doctor.

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: cli_smoke.sh [--help-only] [--doctor] [--cmd browser-use]

Checks:
  --help-only        Run only command/subcommand help checks (default).
  --doctor           Also run `browser-use doctor` after help checks.
  --cmd CMD          CLI command to test, e.g. browser-use or bu.

Examples:
  ./cli_smoke.sh
  ./cli_smoke.sh --cmd bu
  ./cli_smoke.sh --doctor
EOF
}

mode="help-only"
cli_cmd="${BROWSER_USE_CLI:-browser-use}"
cli_parts=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --help-only)
      mode="help-only"
      shift
      ;;
    --doctor)
      mode="doctor"
      shift
      ;;
    --cmd)
      if [[ $# -lt 2 ]]; then
        echo "error: --cmd requires a value" >&2
        exit 2
      fi
      cli_cmd="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "error: unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

run_check() {
  local label="$1"
  shift
  echo "==> $label"
  "$@" >/tmp/browser_use_cli_smoke.out 2>/tmp/browser_use_cli_smoke.err || {
    local status=$?
    echo "FAILED: $label (exit $status)" >&2
    echo "--- stdout ---" >&2
    cat /tmp/browser_use_cli_smoke.out >&2 || true
    echo "--- stderr ---" >&2
    cat /tmp/browser_use_cli_smoke.err >&2 || true
    exit "$status"
  }
}

if command -v "$cli_cmd" >/dev/null 2>&1; then
  cli_parts=("$cli_cmd")
elif [[ "$cli_cmd" == "browser-use" ]] && python -c 'import browser_use' >/dev/null 2>&1; then
  cli_parts=(python -m browser_use.skill_cli.main)
elif [[ "$cli_cmd" == "browser-use" ]] && command -v uv >/dev/null 2>&1 && uv run python -c 'import browser_use' >/dev/null 2>&1; then
  cli_parts=(uv run python -m browser_use.skill_cli.main)
else
  echo "error: command not found: $cli_cmd" >&2
  echo "Try: uv pip install 'browser-use[cli]'" >&2
  exit 127
fi

run_check "main help" "${cli_parts[@]}" --help
run_check "init help" "${cli_parts[@]}" init --help
run_check "cloud v2 help" "${cli_parts[@]}" cloud v2 --help
run_check "sessions help parse" "${cli_parts[@]}" --json sessions

if [[ "$mode" == "doctor" ]]; then
  run_check "doctor" "${cli_parts[@]}" doctor
fi

rm -f /tmp/browser_use_cli_smoke.out /tmp/browser_use_cli_smoke.err

echo "Browser Use CLI smoke checks passed for: $cli_cmd"
