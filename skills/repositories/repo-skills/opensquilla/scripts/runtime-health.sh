#!/bin/sh
# Read-only OpenSquilla runtime snapshot. This script never starts the gateway,
# changes configuration, installs dependencies, or performs live provider calls.
set -u

BIN=${OPENSQUILLA_BIN:-opensquilla}

if ! command -v "$BIN" >/dev/null 2>&1; then
  printf '%s\n' "ERROR: '$BIN' was not found on PATH." >&2
  printf '%s\n' "Set OPENSQUILLA_BIN to an executable path if needed." >&2
  exit 1
fi

printf '%s\n' '== executable =='
command -v "$BIN"


printf '%s\n' '== root help =='
if ! "$BIN" --help >/dev/null 2>&1; then
  printf '%s\n' 'ERROR: root CLI help failed.' >&2
  exit 1
fi
printf '%s\n' 'ok'

run_optional() {
  label=$1
  shift
  printf '\n== %s ==\n' "$label"
  "$BIN" "$@"
  code=$?
  if [ "$code" -eq 0 ]; then
    return 0
  fi
  printf 'NOTE: command exited %s; this can be expected when setup or the gateway is unavailable.\n' "$code" >&2
  return 0
}

run_optional 'onboarding status' onboard status
run_optional 'gateway status' gateway status
run_optional 'doctor (read-only)' doctor --json
run_optional 'provider catalog' providers list --json
run_optional 'search catalog' search list --json
run_optional 'skill catalog' skills list --json

printf '\n%s\n' 'Snapshot complete. Catalog output is not proof of live credentials or network readiness.'
