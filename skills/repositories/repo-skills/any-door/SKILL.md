---
name: any-door
description: "Routes AnyDoor zero-shot object-level image customization workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# AnyDoor

AnyDoor is a zero-shot object-level image customization repo built around a
control-diffusion pipeline, DINOv2 conditioning, mask-aware preprocessing,
local Gradio demo support, and mixed-dataset training utilities.

Use this root skill as a router, not as a full manual. It points future agents
to the smallest workflow-specific sub-skill that owns the task.

## Start here

Read the root references first when you need the whole repo shape:

- `references/overview.md` for the top-level repository map and workflow split.
- `references/environment-and-installation.md` for supported install paths,
  Python/CUDA expectations, and the safest preflight order.
- `references/checkpoints-and-configs.md` for config placeholders, checkpoint
  files, and the paths that must be patched before generation.
- `references/troubleshooting.md` for cross-cutting import, checkpoint, and
  path failures.
- `references/repo-provenance.md` and `references/repo-routing-metadata.json`
  when you need staleness or router-placement metadata.

Run `scripts/check_anydoor_environment.py` before any generation or training
workflow. It checks the repo layout, CUDA readiness, optional xformers, and
placeholder config paths without running a full model.

If placeholder config values are still present, use
`scripts/patch_anydoor_configs.py` to replace them before routing into an
inference or training branch.

## Routing map

| User intent | Route to | Read next |
| --- | --- | --- |
| Fresh clone, install, import, checkpoint, or CUDA questions | `sub-skills/setup-and-checkpoints/` | `references/environment-and-installation.md` and `references/checkpoints-and-configs.md` |
| Single-image customization, VITON-HD inference, Gradio demo, or Cog prediction | `sub-skills/inference-and-demo/` | `sub-skills/inference-and-demo/references/inference-workflows.md`, `sub-skills/inference-and-demo/references/mask-and-image-formats.md`, `sub-skills/inference-and-demo/references/demo-and-cog-deployment.md` |
| Dataset layout, preprocessing, training, debug sampling, or checkpoint conversion | `sub-skills/data-and-training/` | `sub-skills/data-and-training/references/dataset-formats.md`, `sub-skills/data-and-training/references/training-workflows.md`, `sub-skills/data-and-training/references/model-architecture.md` |

## What this root skill owns

- Project-wide repo orientation and workflow routing.
- Shared preflight checks for imports, CUDA, placeholder configs, and checkpoint
  presence.
- Cross-cutting troubleshooting for install, import, backend, and path issues.
- A consistent entry point for future agents so they do not have to rediscover
  the repo layout.

## What this root skill does not own

- Detailed inference preprocessing and output composition.
- Dataset family-specific path rules and training recipes.
- Model architecture internals beyond what is needed to explain AnyDoor
  configuration and path requirements.

## Common signals and destinations

- "I cannot import the repo" or "xformers is missing" → read setup first.
- "Generate from a reference image and mask" → go to inference and demo.
- "How do I prepare UVO / VITON-HD / SAM / MVImageNet data?" → go to data and
  training.
- "How do I patch checkpoint placeholders?" → go to setup and checkpoints.
- "How do I launch the demo or Cog predictor?" → go to inference and demo.
- "How do I start training or convert weights?" → go to data and training.

## Short policy reminders

- Any actual generation in this repo is CUDA-backed; CPU checks are useful for
  support workflows only.
- Do not assume the placeholder checkpoint values in the configs are usable.
- Do not assume bundled examples or datasets are present on the target machine.
- Keep runtime links inside this skill tree only.

## If you need deeper detail

Each sub-skill has its own focused references and scripts. Read the nearest one
instead of turning this router into a manual.
