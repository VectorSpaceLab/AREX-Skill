#!/usr/bin/env bash
set -euo pipefail

# vLLM-backed c2i serving wrapper.
# Normalizes repo-root invocation and keeps checkpoint expectations visible:
# - use a local checkpoint path for --gpt-ckpt
# - pass --from-fsdp when the checkpoint is a raw consolidated FSDP weight
# - the serving JSON must match the requested --gpt-model family

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../../.." && pwd)"
cd "$repo_root"
export PYTHONPATH="$repo_root${PYTHONPATH:+:$PYTHONPATH}"

exec python3 autoregressive/serve/sample_c2i.py "$@" --gpt-type c2i
