---
name: inference
description: "Generate images from Custom Diffusion delta checkpoints for SD
  1.x-style and SDXL models, including prompt files, compressed deltas, and
  pipeline load behavior."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Inference

Use this sub-skill when you already have a Custom Diffusion delta checkpoint and need image generation.

It covers:

- single-prompt and prompt-file sampling
- compressed and uncompressed delta checkpoints
- SD 1.x-style and SDXL sampling paths
- output naming and sample-layout expectations

It does not cover training or delta math. Route those tasks to [`../training/SKILL.md`](../training/SKILL.md) and [`../checkpoint-tools/SKILL.md`](../checkpoint-tools/SKILL.md).

## Start here

1. Read [`references/api-reference.md`](references/api-reference.md).
2. Read [`references/workflows.md`](references/workflows.md).
3. Run [`../checkpoint-tools/scripts/check_delta_layout.py`](../checkpoint-tools/scripts/check_delta_layout.py) before a long sampling run.
4. Check [`references/troubleshooting.md`](references/troubleshooting.md) when the delta layout, model cache, or prompt file is wrong.

## Runtime notes

- The source sampler uses CUDA, a fixed seed, 200 inference steps, and guidance scale 6.
- A compressed delta needs the matching compression flag or a layout checker will flag the `u` / `v` payload.
- The SDXL path uses the XL pipeline and the dual-text-encoder load behavior described in the API reference.
