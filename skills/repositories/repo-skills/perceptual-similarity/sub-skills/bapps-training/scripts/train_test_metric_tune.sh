#!/usr/bin/env bash
set -euo pipefail

# Smoke-friendly trunk-tuning wrapper.

export TRAIN_TRUNK=1
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "${SCRIPT_DIR}/train_test_metric.sh" "$@"
