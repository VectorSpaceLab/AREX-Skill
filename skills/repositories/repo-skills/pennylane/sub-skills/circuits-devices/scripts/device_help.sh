#!/usr/bin/env bash
set -euo pipefail
if ! command -v pl-device-test >/dev/null 2>&1; then
  echo "pl-device-test is not on PATH. Install PennyLane in the active environment." >&2
  exit 2
fi
pl-device-test --help
