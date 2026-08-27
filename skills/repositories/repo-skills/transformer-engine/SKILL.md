---
name: transformer-engine
description: "Route Transformer Engine installation/build, PyTorch, JAX, and
  shared precision/compatibility workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Transformer Engine

Use this skill for NVIDIA Transformer Engine questions. Start here when the user mentions Transformer Engine, TE, the `transformer_engine` package, or a current-source checkout that must be installed, inspected, or explained.

## Route map

| User need | Go to |
| --- | --- |
| Install, build, or verify the package or a source checkout | [install-build](sub-skills/install-build/SKILL.md) |
| Use Transformer Engine with PyTorch | [pytorch](sub-skills/pytorch/SKILL.md) |
| Use Transformer Engine with JAX/Flax | [jax](sub-skills/jax/SKILL.md) |
| Choose a recipe, format, or hardware gate | [precision recipes](references/precision-recipes.md) |
| Diagnose loader, version, CUDA, or recipe failures | [troubleshooting](references/troubleshooting.md) |

## Fast start

1. If the runtime stack is unclear, run the bundled runtime inspector in `scripts/inspect_transformer_engine_runtime.py`.
2. If the task is about installation or source builds, read the install/build sub-skill first.
3. If the task is framework-specific, route directly to the PyTorch or JAX sub-skill rather than trying to infer from common package names alone.
4. If the task is about FP8, MXFP8, NVFP4, BF16, or hardware compatibility, read the shared precision reference before choosing a recipe.

## What this skill does not do

- It does not tell users to open original repo docs, examples, or tests as the runtime answer.
- It does not make FP8/MXFP8/NVFP4 claims without a support probe or hardware gate.
- It does not hide install or import problems behind generic advice when a bundled script or reference can be used instead.

## Architecture notes

- A100/SM80 is BF16/FP16-capable but not an FP8/MXFP8/NVFP4 runtime target.
- FP8 requires compute capability 8.9 or newer.
- NCCL EP is a Hopper-or-newer feature.
- Mixed PyTorch/JAX environments are normal for this repo; use the sub-skill that matches the framework the user actually wants.

## Shared references

- [references/precision-recipes.md](references/precision-recipes.md) for recipe classes, support checks, and hardware selection.
- [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting loader, CUDA, cuBLAS, cuDNN, and version failures.
- [scripts/inspect_transformer_engine_runtime.py](scripts/inspect_transformer_engine_runtime.py) for a quick import/support probe that does not depend on the source checkout.
