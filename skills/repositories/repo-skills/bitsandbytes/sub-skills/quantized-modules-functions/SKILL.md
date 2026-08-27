---
name: quantized-modules-functions
description: "Direct use of bitsandbytes quantized PyTorch modules, autograd
  matmul helpers, and functional quantization primitives for custom modules and
  research code."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Quantized Modules and Functional Primitives

Use this sub-skill when the task needs direct `bitsandbytes.nn`, `bitsandbytes.functional`, `bitsandbytes.matmul`, `bitsandbytes.matmul_4bit`, or `torch.ops.bitsandbytes` APIs rather than Hugging Face model-loading wrappers.

## Choose this sub-skill for

- Replacing `torch.nn.Linear` or `torch.nn.Embedding` with `Linear8bitLt`, `Linear4bit`, `LinearNF4`, `LinearFP4`, `Embedding8bit`, `Embedding4bit`, `EmbeddingNF4`, or `EmbeddingFP4` in custom PyTorch code.
- Working directly with `Int8Params`, `Params4bit`, `QuantState`, `matmul`, `matmul_4bit`, int8 vectorwise quantization, 4-bit quantization, or blockwise quantization primitives.
- Debugging direct module state dicts, quantized checkpoints, `SCB`/`CB` fields, `.to(device)` quantization timing, `quant_state` handling, blocksize rules, or quantized tensor storage dtype.
- Creating CPU-safe construction/signature checks for agents or CI without requiring quantized GPU kernels.

## Route elsewhere

- Hugging Face `BitsAndBytesConfig`, `load_in_8bit`, `load_in_4bit`, QLoRA model loading, PEFT, Accelerate, Diffusers, and FSDP-QLoRA workflows route to `transformers-integrations`.
- Package installation, backend compatibility, missing native library, CUDA/ROCm/XPU/HPU/MPS setup, and `python -m bitsandbytes` failures route to `installation-diagnostics`.
- `Adam8bit`, `AdamW8bit`, paged optimizers, `GlobalOptimManager`, `StableEmbedding`, and training-loop optimizer behavior route to `optimizers-training`.

## Start here

1. Read `references/api-reference.md` for verified constructor/function signatures and parameter notes.
2. Use `references/workflows.md` for direct layer replacement, quantize-on-`.to(device)`, save/load caveats, and primitive recipes.
3. Use `references/troubleshooting.md` to map common symptoms to recovery steps.
4. Run `scripts/quantized-module-smoke.py` for a deterministic CPU-safe import/construction/signature check; pass `--device cuda` or another backend only when that backend is available and native quantized kernels are expected to work.
