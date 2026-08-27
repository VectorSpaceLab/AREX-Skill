---
name: optimizers-training
description: "Choose and use bitsandbytes optimizers in PyTorch training loops,
  including 8-bit, 32-bit, paged variants, StableEmbedding, GlobalOptimManager
  overrides, and optimizer-state checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Optimizers Training

Use this sub-skill when a user asks how to train with `bitsandbytes.optim`, replace a PyTorch optimizer with an 8-bit or paged optimizer, keep specific parameters in 32-bit, use `StableEmbedding`, or validate optimizer state after a training step.

## Route First

- For direct quantized layers, `bitsandbytes.nn.Linear8bitLt`, `Linear4bit`, quantization functions, or low-level matmul APIs, use `../quantized-modules-functions/`.
- For Hugging Face `BitsAndBytesConfig`, QLoRA model loading, PEFT, Accelerate, Diffusers, or FSDP-QLoRA, use `../transformers-integrations/`.
- For install/import failures, backend library loading, `python -m bitsandbytes`, CUDA/ROCm/XPU compatibility, or native-kernel diagnostics, use `../installation-diagnostics/`.

## References

- Read `references/optimizer-api.md` for optimizer families, verified signatures, defaults, and state knobs.
- Read `references/optimizer-workflows.md` for drop-in replacement patterns, `min_8bit_size`, `StableEmbedding`, `GlobalOptimManager`, paged optimizers, and validation steps.
- Read `references/troubleshooting.md` when memory savings are missing, overrides do not apply, state dicts fail, CPU/GPU expectations mismatch, or paged optimizers do not behave as expected.

## Bundled Script

- Run `python sub-skills/optimizers-training/scripts/cpu-optimizer-smoke.py --optimizer adam8bit --steps 3` for a tiny deterministic CPU smoke that imports bitsandbytes, trains a toy model without downloads, and reports optimizer state dtypes/devices.
- Use `--optimizer adam32bit` to compare the same toy loop with a 32-bit bitsandbytes Adam optimizer.
- Use `--force-8bit-small-tensors` only as a diagnostic to lower `min_8bit_size` for the toy model; real training should usually keep the default unless memory analysis justifies changing it.

## Quick Decision Rules

- Start with `bnb.optim.Adam8bit` or `bnb.optim.AdamW8bit` as a drop-in replacement when optimizer-state memory is a bottleneck and parameters dominate memory use.
- Keep the default `min_8bit_size=4096` unless the user understands that smaller tensors are intentionally left in 32-bit for stability and minimal savings.
- Use `bnb.nn.StableEmbedding` for NLP embedding layers when training with 8-bit optimizer states.
- Use `GlobalOptimManager` when embeddings, layer norm, biases, or other unstable parameters should stay 32-bit while the rest of the model uses 8-bit states.
- Use paged optimizers only for supported accelerators and memory-pressure workflows; do not promise gains on CPU-only runs or when activations dominate memory.
