#!/usr/bin/env bash
# Safe installed-package smoke checks for Potpie. Does not start the daemon.
set -euo pipefail

POTPIE_BIN="${POTPIE_BIN:-potpie}"

if ! command -v "$POTPIE_BIN" >/dev/null 2>&1; then
  echo "Potpie CLI not found: $POTPIE_BIN" >&2
  echo "Install with: uv tool install potpie  # or python -m pip install potpie" >&2
  exit 127
fi

echo "== Potpie version =="
"$POTPIE_BIN" --version

echo "== Help surfaces =="
"$POTPIE_BIN" --help >/dev/null
for group in pot source daemon graph ledger backend skills telemetry; do
  "$POTPIE_BIN" "$group" --help >/dev/null
  echo "help ok: potpie $group"
done

echo "== Daemon status probe =="
if "$POTPIE_BIN" daemon status; then
  echo "daemon status command completed"
else
  echo "daemon status command returned non-zero; inspect runtime before daemon-dependent commands" >&2
  exit 1
fi

cat <<'NOTE'

Smoke completed. If `potpie status`, `potpie doctor`, `potpie backend list`,
or `potpie skills status` report unavailable after this check, diagnose daemon
startup/readiness instead of treating the package import as broken.
NOTE
