---
name: distributed-blocks
description: "Operate Petals RemoteSequential block sequences, local block
  loading, quantization, tensor-parallel conversion, dtype constraints, and
  speculative Llama block internals."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Petals Distributed Blocks

Use this sub-skill for block-level Petals tasks involving `RemoteSequential`, remote transformer block chains, hidden-state tensors, `load_pretrained_block`, `QuantType`, `convert_block`, tensor-parallel devices, DHT prefix alignment, or speculative Llama internals.

Read [references/api-reference.md](references/api-reference.md), [references/workflows.md](references/workflows.md), and [references/troubleshooting.md](references/troubleshooting.md). Use `python scripts/inspect_block_api.py --help` for a no-network API inspection.

Route ordinary `.generate()` usage to `client-inference`, server launch flags to `server-swarms`, prompt training to `prompt-tuning`, and benchmarks to `benchmarks-maintenance`.

Checklist: `RemoteSequential.forward()` takes hidden states shaped `[batch, seq, hidden]`; block slices must be inside model layer bounds; clients and servers must agree on DHT prefix and block indices; deep prompts must match sliced block count; quantization requires a compatible optional backend.
