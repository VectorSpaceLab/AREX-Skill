#!/usr/bin/env bash
set -euo pipefail

# Single-process c2i sampling wrapper.
# The tokenizer checkpoint is pinned to the released class-conditional VQ-16 weights.
# Checkpoint loader supports model / module / state_dict, or raw FSDP with --from-fsdp.

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../../.." && pwd)"
cd "$repo_root"
export PYTHONPATH="$repo_root${PYTHONPATH:+:$PYTHONPATH}"

exec python3 autoregressive/sample/sample_c2i.py \
  --vq-ckpt ./pretrained_models/vq_ds16_c2i.pt \
  "$@" --gpt-type c2i
