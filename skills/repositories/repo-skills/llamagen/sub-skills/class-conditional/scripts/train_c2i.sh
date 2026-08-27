#!/usr/bin/env bash
set -euo pipefail

# DDP c2i training wrapper.
# Distributed env vars expected by torchrun:
#   nnodes, nproc_per_node, node_rank, master_addr, master_port
# Typical class-conditional flow:
#   bash scripts/train_c2i.sh --cloud-save-path ... --code-path ... --gpt-model GPT-L ...

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../../.." && pwd)"
cd "$repo_root"
export PYTHONPATH="$repo_root${PYTHONPATH:+:$PYTHONPATH}"

: "${nnodes:?set nnodes before calling this wrapper}"
: "${nproc_per_node:?set nproc_per_node before calling this wrapper}"
: "${node_rank:?set node_rank before calling this wrapper}"
: "${master_addr:?set master_addr before calling this wrapper}"
: "${master_port:?set master_port before calling this wrapper}"

exec torchrun \
  --nnodes="$nnodes" \
  --nproc_per_node="$nproc_per_node" \
  --node_rank="$node_rank" \
  --master_addr="$master_addr" \
  --master_port="$master_port" \
  autoregressive/train/train_c2i.py "$@" --gpt-type c2i
