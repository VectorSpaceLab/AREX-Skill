#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON:-python}"
MODULE="ochat.serving.openai_api_server"

has_help=0
has_model=0
expect_model_value=0

for arg in "$@"; do
  if [[ "$expect_model_value" -eq 1 ]]; then
    if [[ -n "$arg" && "$arg" != --* ]]; then
      has_model=1
    fi
    expect_model_value=0
    continue
  fi

  case "$arg" in
    -h|--help)
      has_help=1
      ;;
    --model)
      expect_model_value=1
      ;;
    --model=*)
      value="${arg#--model=}"
      if [[ -n "$value" ]]; then
        has_model=1
      fi
      ;;
  esac
done

if [[ "$has_help" -eq 1 ]]; then
  exec "$PYTHON_BIN" -m "$MODULE" "$@"
fi

if [[ "$has_model" -ne 1 ]]; then
  cat >&2 <<'USAGE'
Error: --model is required to launch the OpenChat API server.

Examples:
  run_openchat_server.sh --help
  run_openchat_server.sh --model openchat/openchat-3.6-8b-20240522 --host localhost --port 18888
  run_openchat_server.sh --model MODEL_REPO_OR_DIR --model-type openchat_3.6

Actual serving requires model weights, a compatible CUDA/PyTorch/vLLM/Ray environment,
and enough GPU memory for the selected model and request load.
USAGE
  exit 2
fi

exec "$PYTHON_BIN" -m "$MODULE" "$@"
