#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON:-python}"

if [[ $# -eq 0 ]]; then
  echo "No arguments supplied; showing OpenChat evaluation help." >&2
  exec "$PYTHON_BIN" -m ochat.evaluation.run_eval --help
fi

exec "$PYTHON_BIN" -m ochat.evaluation.run_eval "$@"
