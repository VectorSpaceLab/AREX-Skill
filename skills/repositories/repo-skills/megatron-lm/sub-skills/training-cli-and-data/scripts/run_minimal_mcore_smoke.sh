#!/usr/bin/env bash
# Run a tiny Megatron Core training smoke from a Megatron-LM checkout.
# This wrapper uses a temporary working directory for outputs and requires
# a CUDA-capable Python environment with Megatron-LM installed/editable.
set -euo pipefail

NPROC_PER_NODE="${NPROC_PER_NODE:-2}"
ENTRYPOINT="${ENTRYPOINT:-examples/run_simple_mcore_train_loop.py}"
WORKDIR="${WORKDIR:-$(mktemp -d -t megatron-mcore-smoke-XXXXXX)}"

if ! command -v python >/dev/null 2>&1; then
  echo "python is not on PATH" >&2
  exit 2
fi
python - <<'PY'
import torch
if not torch.cuda.is_available() or torch.cuda.device_count() < 2:
    raise SystemExit("Need at least two visible CUDA GPUs for the default smoke")
print("CUDA devices:", torch.cuda.device_count(), torch.cuda.get_device_name(0))
PY

if [ ! -f "$ENTRYPOINT" ]; then
  echo "Expected entrypoint $ENTRYPOINT in the active Megatron-LM checkout" >&2
  exit 2
fi

echo "Using temporary output directory: $WORKDIR"
(
  cd "$WORKDIR"
  python -m torch.distributed.run --nproc-per-node "$NPROC_PER_NODE" "$OLDPWD/$ENTRYPOINT"
)
