---
name: model-internals
description: "Maintain and diagnose nano-vLLM internals, including Qwen3
  architecture, tensor-parallel layers, FlashAttention/Triton context, KV cache,
  and safetensors weight loading."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Model internals

Use this route when the task is to modify, diagnose, or extend nano-vLLM source
behavior rather than simply run generation. The implementation is intentionally
small and Qwen3-focused; many failures come from assuming it is a general
Transformers runtime.

## Fast path

1. Identify whether the issue is model compatibility, weight naming, tensor
   parallel sharding, attention context, or runtime scheduling.
2. For a candidate model, run
   [scripts/inspect_model_contract.py](scripts/inspect_model_contract.py) with
   the intended `--tensor-parallel-size` before loading weights.
3. Read [references/architecture.md](references/architecture.md) for the
   forward path, attention context, KV-cache, and sharding contracts.
4. Read [references/weight-loading.md](references/weight-loading.md) when a
   safetensors key is missing, renamed, or needs a new packed-module mapping.
5. Use [references/troubleshooting.md](references/troubleshooting.md) to map
   common backend/import/dist failures to the owning layer.

Route user-facing prompt generation to
[../offline-inference/SKILL.md](../offline-inference/SKILL.md). Route runtime
batch sizing, graph capture, and benchmarking to
[../performance-tuning/SKILL.md](../performance-tuning/SKILL.md).

## Compatibility checklist

- The Hugging Face config should be Qwen3-like, with attention head counts,
  key-value head counts, hidden size, intermediate size, and vocabulary size
  divisible by the selected tensor-parallel size where the sharded layers need
  it.
- The model uses packed QKV and gate/up projections internally. Weight names
  containing `q_proj`, `k_proj`, `v_proj`, `gate_proj`, or `up_proj` are mapped
  into packed parameters; all other names must match a parameter directly.
- Attention uses FlashAttention varlen prefill and KV-cache decode paths, plus a
  Triton kernel to store keys/values into block slots. Context fields must be
  set correctly before calling attention.
- The runner sets the default device to CUDA while building/loading/running the
  model and resets it afterward. Avoid hidden CPU tensor creation inside model
  code unless explicitly moved.

## Extension rules

When adding another model family, treat it as a full compatibility project:
create a model module, define packed-module mappings, validate dimension
sharding, verify safetensors names, and add smoke coverage for prefill, decode,
KV-cache allocation, and sampling. Do not only add an AutoConfig branch.
