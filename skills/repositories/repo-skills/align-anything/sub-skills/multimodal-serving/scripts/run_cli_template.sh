#!/usr/bin/env bash
# Launch an align-anything serving CLI from an installed package.
# This script is self-contained and does not depend on the source checkout.

set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  MODEL_NAME_OR_PATH=<model> SERVE_MODE=text  bash run_cli_template.sh
  MODEL_NAME_OR_PATH=<model> SERVE_MODE=multi MODALITY=image bash run_cli_template.sh
  MODEL_NAME_OR_PATH=<model> SERVE_MODE=omni  bash run_cli_template.sh

Environment variables:
  MODEL_NAME_OR_PATH   Required. Hugging Face model id or local model directory.
  SERVE_MODE           text | multi | omni. Default: text.
  MODALITY             For SERVE_MODE=multi: image | audio | video | text. Default: image.
  ZERO_STAGE           Optional. Defaults to 0; useful for MiniCPM wrappers.
  LOCAL_RANK           Optional accelerator index used by align-anything device utilities.
  CUDA_VISIBLE_DEVICES Optional GPU selection, for example 0 or 0,1.
  GRADIO_SERVER_NAME   Optional Gradio bind host, for example 127.0.0.1 or 0.0.0.0.
  GRADIO_SERVER_PORT   Optional Gradio port, for example 7860.
  PYTHON               Optional Python executable. Default: python.

Notes:
  - The packaged CLIs call Gradio launch(share=True), so a shareable link may be created.
  - Use trusted model repositories when remote code is required.
  - Run check_model_loading.py first when debugging dependency, dtype, or device issues.
USAGE
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

PYTHON_BIN="${PYTHON:-python}"
SERVE_MODE="${SERVE_MODE:-text}"
MODALITY="${MODALITY:-image}"
ZERO_STAGE="${ZERO_STAGE:-0}"
export ZERO_STAGE

if [[ -z "${MODEL_NAME_OR_PATH:-}" ]]; then
  echo "ERROR: MODEL_NAME_OR_PATH is required." >&2
  usage >&2
  exit 2
fi
export MODEL_NAME_OR_PATH

case "${SERVE_MODE}" in
  text)
    echo "[align-anything] launching text-modal CLI for ${MODEL_NAME_OR_PATH}" >&2
    exec "${PYTHON_BIN}" -m align_anything.serve.text_modal_cli \
      --model_name_or_path "${MODEL_NAME_OR_PATH}"
    ;;
  multi)
    case "${MODALITY}" in
      image|audio|video|text) ;;
      *)
        echo "ERROR: MODALITY must be one of image, audio, video, text for SERVE_MODE=multi." >&2
        exit 2
        ;;
    esac
    echo "[align-anything] launching multi-modal CLI for ${MODEL_NAME_OR_PATH} modality=${MODALITY}" >&2
    exec "${PYTHON_BIN}" -m align_anything.serve.multi_modal_cli \
      --model_name_or_path "${MODEL_NAME_OR_PATH}" \
      --modality "${MODALITY}"
    ;;
  omni)
    echo "[align-anything] launching omni-modal CLI for ${MODEL_NAME_OR_PATH}" >&2
    exec "${PYTHON_BIN}" -m align_anything.serve.omni_modal_cli \
      --model_name_or_path "${MODEL_NAME_OR_PATH}"
    ;;
  *)
    echo "ERROR: SERVE_MODE must be text, multi, or omni." >&2
    usage >&2
    exit 2
    ;;
esac
