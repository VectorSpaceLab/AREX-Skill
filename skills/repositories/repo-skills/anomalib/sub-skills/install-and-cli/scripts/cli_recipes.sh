#!/usr/bin/env bash
# Read-only printer for copyable Anomalib CLI and install recipes.
#
# This helper never runs pip, uv, or anomalib. It only prints the current
# command patterns for install, train, predict, export, and benchmark.
#
# Example:
#   ./cli_recipes.sh install
#   ./cli_recipes.sh predict

set -euo pipefail

section="${1:-all}"

usage() {
  cat <<'EOF'
Usage: cli_recipes.sh [all|install|train|predict|export|benchmark]

Prints copyable command recipes. No network calls and no training runs.
EOF
}

print_install() {
  cat <<'EOF'
# Fresh CPU install
uv pip install "anomalib[cpu]"
pip install "anomalib[cpu]"

# Fresh CPU + OpenVINO install
uv pip install "anomalib[cpu,openvino]"
pip install "anomalib[cpu,openvino]"

# Editable source installs
uv sync --extra cpu
uv sync --extra cpu --extra openvino
pip install -e ".[cpu]"
pip install -e ".[cpu,openvino]"

# Add-on bundles inside an already working environment
anomalib install --option full
anomalib install --option core   # base dependencies only; not a backend selector
anomalib install --option dev
anomalib install --option loggers
anomalib install --option notebooks
anomalib install --option openvino
anomalib install -v --option openvino
EOF
}

print_train() {
  cat <<'EOF'
# Lightning-style fit / evaluate / test split
anomalib fit --model anomalib.models.Padim --data anomalib.data.MVTecAD
anomalib validate --model anomalib.models.Padim --data anomalib.data.MVTecAD --ckpt_path <PATH_TO_CHECKPOINT>
anomalib test --model anomalib.models.Padim --data anomalib.data.MVTecAD --ckpt_path <PATH_TO_CHECKPOINT>

# End-to-end Anomalib training flow
anomalib train --model Patchcore --data anomalib.data.MVTecAD
anomalib train --model EfficientAd --data anomalib.data.MVTecAD --data.category hazelnut --data.train_batch_size 1 --trainer.max_epochs 200
anomalib train --config path/to/config.yaml
EOF
}

print_predict() {
  cat <<'EOF'
# Current predict CLI syntax
anomalib predict --model anomalib.models.Patchcore \
                 --data anomalib.data.MVTecAD \
                 --ckpt_path <path/to/model.ckpt>

anomalib predict --model anomalib.models.Patchcore \
                 --data anomalib.data.MVTecAD \
                 --ckpt_path <path/to/model.ckpt> \
                 --return_predictions

anomalib predict --config <path/to/config> --return_predictions
EOF
}

print_export() {
  cat <<'EOF'
# Torch, ONNX, and OpenVINO export examples
anomalib export --model Padim --export_type torch --ckpt_path <PATH_TO_CHECKPOINT>
anomalib export --model Padim --export_type onnx --ckpt_path <PATH_TO_CHECKPOINT> --input_size "[256,256]"
anomalib export --model Padim --export_type openvino --ckpt_path <PATH_TO_CHECKPOINT> --input_size "[256,256]" --compression_type FP16
anomalib export --model Padim --export_type openvino --ckpt_path <PATH_TO_CHECKPOINT> --input_size "[256,256]" --compression_type INT8_PTQ --data MVTecAD

# OpenVINO Model Optimizer arguments live under --ov_kwargs.<name>
EOF
}

print_benchmark() {
  cat <<'EOF'
# Experimental benchmark pipeline entrypoint
anomalib benchmark --config path/to/benchmark.yaml

# Detailed pipeline configuration and runner behavior live in the benchmark sub-skill.
EOF
}

case "$section" in
  all)
    print_install
    printf '\n'
    print_train
    printf '\n'
    print_predict
    printf '\n'
    print_export
    printf '\n'
    print_benchmark
    ;;
  install)
    print_install
    ;;
  train)
    print_train
    ;;
  predict)
    print_predict
    ;;
  export)
    print_export
    ;;
  benchmark)
    print_benchmark
    ;;
  -h|--help|help)
    usage
    ;;
  *)
    echo "Unknown section: $section" >&2
    usage >&2
    exit 2
    ;;
esac
