#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <config.py> [seed]" >&2
  exit 1
fi

config_path="$1"
seed="${2:-0}"

ding -m parallel -c "$config_path" -s "$seed"
