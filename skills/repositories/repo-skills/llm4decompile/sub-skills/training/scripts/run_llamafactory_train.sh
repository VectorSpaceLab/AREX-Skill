#!/usr/bin/env bash
set -euo pipefail

CONFIG_FILE="${1:-${CONFIG_FILE:-}}"
if [[ -z "${CONFIG_FILE}" ]]; then
  echo "usage: run_llamafactory_train.sh <config.yaml>" >&2
  echo "       or set CONFIG_FILE in the environment" >&2
  exit 1
fi

if ! command -v llamafactory-cli >/dev/null 2>&1; then
  echo "error: llamafactory-cli not found in PATH" >&2
  exit 1
fi

llamafactory-cli train "${CONFIG_FILE}"
