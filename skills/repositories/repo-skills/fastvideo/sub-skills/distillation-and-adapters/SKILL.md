---
name: distillation-and-adapters
description: "Guides FastVideo DMD and self-forcing distillation, Attn-QAT, LoRA extraction/merge/verification, and checkpoint conversion planning."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Distillation and adapters

Use for post-training methods, sparse/distilled model workflows, quantization-
aware attention, LoRA lifecycle, and official-to-FastVideo checkpoint handling.
These workflows are GPU-, data-, and storage-intensive; begin with a dry-run
and a clear checkpoint/output plan.

## Choose the operation

- DMD/sparse distillation: teacher/student/critic and precomputed data; inspect
  timestep, guidance, sparsity, and multi-GPU settings.
- Self-Forcing: causal generation/distillation with a matching causal model and
  streaming/trajectory assumptions.
- Attn-QAT: fake-quantized attention fine-tuning, followed by a compatible DMD2
  stage when the recipe calls for it.
- LoRA: train an adapter, extract from base versus fine-tuned weights, merge,
  then compare outputs or validate parameter keys.
- Conversion: map official checkpoint keys to the native component state dict,
  preserve explicit skipped-key reasons, validate shapes/norms, and only then
  publish to a model hub.

Read [post-training](references/post-training.md), [LoRA/checkpoints](references/lora-and-checkpoints.md),
[conversion](references/checkpoint-conversion.md), and [troubleshooting](references/troubleshooting.md)
for failure recovery. Use the bundled safe
[checkpoint format helper](scripts/pt_to_safetensors.py) only for local format
conversion; it does not understand model semantics.

Never use a CPU success as proof of CUDA kernel quality or distilled output
quality. Keep teacher/critic/student attention and precision choices explicit.
