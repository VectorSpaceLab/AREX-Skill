---
name: zero123plus
description: "Guides Zero123Plus generation, ControlNet variants, demo launch,
  and Cog deployment workflows for single-image-to-multiview inference."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Zero123Plus

Use this skill when the task mentions Zero123Plus, single-image-to-multiview
inference, depth ControlNet, normal generation, matting cleanup, Streamlit,
Gradio, Docker/Gitpod, or Cog/Replicate deployment.

## Start here

- [`references/dependency-and-runtime.md`](references/dependency-and-runtime.md):
  verified Python/runtime stack, CUDA expectations, and install recipe.
- [`references/troubleshooting.md`](references/troubleshooting.md):
  cross-cutting install/import/cache/backend issues and where to go next.
- [`references/repo-provenance.md`](references/repo-provenance.md):
  snapshot of the source checkout used to build this skill.
- [`scripts/check_zero123plus_env.py`](scripts/check_zero123plus_env.py):
  safe environment checker for torch, CUDA, and the bundled optional modules.

## Route map

- For base image-to-multiview generation, depth ControlNet, normal generation,
  camera layout, and matting cleanup, read
  [`sub-skills/generation/SKILL.md`](sub-skills/generation/SKILL.md).
- For Streamlit, Gradio, Docker/Gitpod, Cog/Replicate, weights, and demo
  deployment behavior, read
  [`sub-skills/deployment/SKILL.md`](sub-skills/deployment/SKILL.md).

## Installation summary

This repository is GPU-first. The verified inspection stack used Python 3.11 and
CUDA-capable PyTorch.

A representative setup is:

1. Create a private Python 3.11 environment.
2. Install a CUDA wheel for PyTorch and torchvision.
3. Install the repo runtime stack summarized in
   `references/dependency-and-runtime.md`.
4. Run `python scripts/check_zero123plus_env.py --check-only` or
   `--require-cuda` before a real generation run.

If you only need the generation path, start with the generation sub-skill. If
you need local demos or deployment, start with the deployment sub-skill.

## Minimal checks

- `python scripts/check_zero123plus_env.py --check-only`
- `python scripts/check_zero123plus_env.py --require-cuda`

## Notes

- The model weights are non-commercial even though the code is Apache 2.0.
- CUDA is required for actual generation; CPU is not a full substitute.
- Bundled scripts default to local-only loading and require `--allow-download`
  before they fetch missing model weights.
