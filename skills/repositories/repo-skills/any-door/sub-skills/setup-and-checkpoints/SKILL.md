---
name: setup-and-checkpoints
description: "Prepares AnyDoor environments, checkpoints, and config paths."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Setup and Checkpoints

Use this sub-skill when the task is about installing AnyDoor, verifying the
runtime environment, locating or patching checkpoint paths, or explaining why a
fresh clone still cannot generate images.

## What this sub-skill owns

- Environment setup for AnyDoor’s torch/CUDA stack.
- Repo layout checks and import readiness.
- Placeholder checkpoint and DINOv2 path patching.
- Optional dependency awareness for xformers and demo mask refinement.
- The preflight stage before any inference, demo, or training route.

## What this sub-skill does not own

- Mask preprocessing for inference inputs.
- Gradio, Cog, or prediction input/output handling.
- Dataset-specific path formats or training recipes.

Route those topics to the sibling sub-skills.

## Read first

- `../../references/environment-and-installation.md`
- `../../references/checkpoints-and-configs.md`
- `../../references/troubleshooting.md`
- `references/checkpoint-checklist.md`
- `references/troubleshooting.md`

## Use these scripts

- `../../scripts/check_anydoor_environment.py` for a safe repo-root preflight.
- `../../scripts/patch_anydoor_configs.py` to replace checkpoint placeholders.

## Trigger phrases

This is usually the right branch when the user says things like:

- “I just cloned the repo.”
- “Why does import or CUDA fail?”
- “Where do I put the AnyDoor checkpoint?”
- “What should I do about the DINOv2 weight?”
- “Can I skip xformers?”
- “The demo says it needs a model but I only see placeholders.”

## Minimum operational checklist

1. Confirm the repo root contains `cldm/`, `ldm/`, `datasets/`, `configs/`, and
   `dinov2/`.
2. Confirm the Python environment imports torch and sees CUDA when generation is
   expected.
3. Check that the placeholder values in `configs/inference.yaml`,
   `configs/demo.yaml`, and `configs/anydoor.yaml` have been replaced.
4. Verify the DINOv2 checkpoint exists at the configured path.
5. If the demo refinement toggle is enabled, verify the optional `iseg` weight.

## Common decisions

- **xformers missing**: usually record and continue. The attention code has a
  fallback path.
- **share package unavailable**: only the source weight-conversion helper is
  affected; the rest of the repo can still be documented and checked.
- **CPU import only**: useful for support checks, but not proof that AnyDoor can
  generate images.
- **Placeholder config values remain**: stop and patch before routing to any
  generation workflow.

## Troubleshooting focus

This branch owns installation and backend problems such as:

- `ModuleNotFoundError` from running outside the repo root.
- CUDA wheel or driver mismatches.
- Optional dependency gaps like `xformers`.
- Missing checkpoint or DINOv2 weights.
- Demo refinement toggle failures due to a missing `iseg` weight.
- The stale conversion-script config path issue.

## Output expected from a future agent

A future agent should be able to say:

- which paths are ready,
- which placeholders are still unresolved,
- whether CUDA is actually available,
- which optional dependencies were skipped,
- and what remains blocked before any generation route.

## Cross-links

When this branch is complete, pass the task to:

- `inference-and-demo` for mask/image generation tasks.
- `data-and-training` for dataset and training tasks.

## Quality bar

The branch is ready when the future agent can prepare a repo root, patch the
configs, and explain any remaining backend or checkpoint limitations without
reopening the source files.
