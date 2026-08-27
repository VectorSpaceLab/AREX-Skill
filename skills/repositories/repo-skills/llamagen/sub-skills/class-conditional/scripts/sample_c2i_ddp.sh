#!/usr/bin/env bash
set -euo pipefail

# DDP c2i sampling wrapper.
# Produces numbered PNGs and, on rank 0, packs them into <sample_dir>.npz.
# Checkpoint loader supports model / module / state_dict, or raw FSDP with --from-fsdp.

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../../.." && pwd)"
cd "$repo_root"
export PYTHONPATH="$repo_root${PYTHONPATH:+:$PYTHONPATH}"

exec torchrun \
  --nnodes=1 \
  --nproc_per_node=8 \
  --node_rank=0 \
  --master_port=12345 \
  autoregressive/sample/sample_c2i_ddp.py \
  --vq-ckpt ./pretrained_models/vq_ds16_c2i.pt \
  "$@" --gpt-type c2i
