---
name: pytorch
description: "Operate transformer_engine.pytorch for PyTorch layers, precision
  control, distributed overlap, and debug workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# PyTorch

Use this sub-skill when the task is to apply Transformer Engine's PyTorch surface inside a model, training loop, export path, or debugging session.

## Route here for

- Replacing `torch.nn` layers with `transformer_engine.pytorch.Linear`, `GroupedLinear`, `LayerNorm`, `RMSNorm`, `LayerNormLinear`, `LayerNormMLP`, `DotProductAttention`, `MultiheadAttention`, or `TransformerLayer`.
- BF16/FP16 training or inference with matching `params_dtype` and `torch.autocast`.
- FP8, MXFP8, or NVFP4 questions, recipe selection, and hardware gating with `te.autocast(...)`.
- Quantized parameter initialization, quantized tensor inspection, and quantizer choices.
- Distributed execution, checkpointing, userbuffers, comm/GEMM overlap, CUDA graphs, CPU offload, or op-fuser work.
- Debugging with Nvidia-DL-Framework-Inspect and Transformer Engine debug features.
- Import, version, backend, and precision-availability troubleshooting.

## Required references

Read these bundled references before changing code or explaining usage:

1. [`references/api-reference.md`](references/api-reference.md) for constructors, helpers, tensor classes, and op-fuser surfaces.
2. [`references/workflows.md`](references/workflows.md) for minimal BF16/FP16 flows and guarded low-precision recipes.
3. [`references/distributed-and-advanced.md`](references/distributed-and-advanced.md) for FSDP, checkpointing, userbuffers, CPU offload, export, and advanced fusion.
4. [`references/troubleshooting.md`](references/troubleshooting.md) for import order, runtime mismatches, and precision failures.

## Smoke helper

Run the bundled smoke script to validate a small BF16 `te.Linear` path without depending on the source repository:

```bash
python scripts/pytorch_bf16_smoke.py --help
python scripts/pytorch_bf16_smoke.py --device cuda --in-features 16 --out-features 32 --batch-size 4
```

The helper prints version, device, and precision-availability facts, then runs a tiny BF16 forward/backward pass. It is intentionally narrower than the full `TransformerLayer` examples.

## Operating cautions

- Use `torch.autocast` for BF16/FP16 compute control; use `te.autocast` for FP8/MXFP8/NVFP4 quantized compute. They are not interchangeable.
- Do not promise FP8 on A100-class hardware. Always check availability first and surface the reason string when a recipe is unavailable.
- When `quantized_model_init(enabled=True)` is used with master-weight optimizers, preserve or copy high-precision init values before clearing them if you need FP32 seeding.
- Prefer the bundled smoke path for environment checks when larger TransformerLayer examples are unstable.
