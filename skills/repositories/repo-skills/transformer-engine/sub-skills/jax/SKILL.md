---
name: jax
description: "Use NVIDIA Transformer Engine JAX and Flax APIs for module
  replacement, BF16/FP16 operation, hardware-gated FP8 recipes, sharding,
  checkpointing, fused attention, and validation."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Transformer Engine JAX/Flax Router

Use this sub-skill when the task involves `transformer_engine.jax` or `transformer_engine.jax.flax` in a JAX/Flax project.

## Route triggers

Load this sub-skill for requests about:

- Replacing Flax modules or GEMMs with TE equivalents, including `DenseGeneral`, `LayerNorm`, `LayerNormDenseGeneral`, `LayerNormMLP`, and `TransformerLayer`.
- BF16 or FP16 flows where TE parameters use a module `dtype` and computation follows the input tensor dtype.
- Low-precision contexts with `te.autocast`, deprecated `fp8_autocast`, hardware-gated FP8/MXFP8/NVFP4 recipes, and quantization metadata collections.
- Training-loop handling of `update_collections`, `NVTE_FP8_COLLECTION_NAME`, `params`, and non-param Flax variable collections.
- Sharding with `MeshResource`, logical axes, `extend_logical_axis_rules`, tensor/data/context parallel resources, or checkpoint policies for TE GEMMs.
- Fused attention, `DotProductAttention`, `MultiHeadAttention`, GQA/MQA layouts, score modification callbacks, sliding-window attention, and fallback behavior.
- Troubleshooting JAX/JAXLIB/CUDA/cuDNN compatibility, XLA preallocation/OOM, FP8 hardware gates, `NVTE_JAX_CUSTOM_CALLS`, fused-attention fallback, and CUDA/cuBLAS/cuBLASLt aborts.

## Read order

1. Start with [references/api-reference.md](references/api-reference.md) for the public JAX/Flax API surface and import names.
2. Use [references/workflows.md](references/workflows.md) for BF16/FP16 replacement patterns, FP8 autocast semantics, collection updates, recipe support guards, and validation commands.
3. Use [references/sharding-and-checkpointing.md](references/sharding-and-checkpointing.md) for `MeshResource`, logical axis rules, distributed caveats, and TE-aware checkpoint policies.
4. Use [references/troubleshooting.md](references/troubleshooting.md) when imports, kernels, recipe support, fused attention, or memory behavior fail.
5. For a minimal runtime check, run the bundled [scripts/jax_bf16_smoke.py](scripts/jax_bf16_smoke.py) in the target environment.

## Operating constraints

- Import `jax` before `transformer_engine.jax` in smoke tests and new scripts.
- Do not assume FP8 support from BF16 success. On A100-class hardware BF16 TE dense can work while `get_supported_quantization_recipes()` may be empty; gate every recipe with a support probe.
- For JAX quantization metadata, initialize TE modules inside `te.autocast(enabled=True, recipe=...)`; then keep non-param variable collections with the training state across steps.
- Prefer bundled synthetic validation over dataset examples by default; dataset-download examples are not the first-line check.
