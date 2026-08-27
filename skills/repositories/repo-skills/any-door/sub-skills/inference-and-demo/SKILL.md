---
name: inference-and-demo
description: "Runs AnyDoor image generation, demo, and prediction workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Inference and Demo

Use this sub-skill when the task is about generating a customized image,
launching the local Gradio demo, or understanding the prediction interface.

## What this sub-skill owns

- Single-image AnyDoor inference.
- VITON-HD-style batch inference.
- Mask and image validation before generation.
- Local Gradio launch behavior and interactive options.
- Cog / Replicate-style prediction input and output contracts.

## What this sub-skill does not own

- Environment installation and checkpoint patching.
- Dataset format design or training data preparation.
- Weight conversion and training launch details.

Route those to the sibling sub-skills.

## Read first

- `../../references/overview.md`
- `../../references/checkpoints-and-configs.md`
- `../../references/troubleshooting.md`
- `references/inference-workflows.md`
- `references/mask-and-image-formats.md`
- `references/demo-and-cog-deployment.md`
- `references/troubleshooting.md`

## Use these scripts

- `scripts/validate_inference_inputs.py` to check image and mask pairs.
- `scripts/run_inference_checked.sh` to validate a repo root before running the
  source inference entry point.
- `scripts/launch_gradio_checked.sh` to validate the same prerequisites before a
  local demo launch.

## Trigger phrases

This is usually the right branch when the user says things like:

- “Generate from this reference object.”
- “How do I run inference on a single image?”
- “I need VITON-HD results.”
- “Launch the local demo.”
- “What does the Cog predictor expect?”
- “Why is my mask or crop wrong?”
- “Can the demo refine the reference mask?”

## Input contract

The main generation route expects:

- a reference image,
- a reference mask or alpha channel,
- a target/background image,
- a target mask,
- and the patched AnyDoor / DINOv2 checkpoints.

The preprocessing contract is mask-aware:

- masks must be non-empty,
- masks must match the image size you intend to use,
- and masks should be binary by the time they reach the generation step.

## Output contract

A successful generation route should explain:

- where the customized image is saved,
- whether the result is a single image or a composite visualization,
- which guidance, strength, and step settings were used,
- and whether the output comes from the standard or shape-control path.

## Default workflow order

1. Run the environment preflight from `setup-and-checkpoints` if you have not
   already done so.
2. Validate the input images and masks.
3. Confirm the checkpoints are patched and accessible.
4. Run the generation or demo launch command.
5. If the result is wrong, inspect the mask and crop assumptions before changing
   model settings.

## Common decisions

- **Reference image has alpha**: derive the reference mask from alpha when that
  is the cleanest representation.
- **Separate reference mask exists**: prefer explicit validation over guessing.
- **Interactive mask refinement**: treat it as optional and explain the weight
  requirement.
- **Shape control**: explain that it changes how the target mask influences the
  collage path.
- **Cog deployment**: document the download/cache assumption so the user knows
  when offline use will fail.

## Troubleshooting focus

This branch owns symptoms such as:

- empty or non-binary masks,
- wrong crop placement,
- target/reference mask dimension mismatches,
- checkpoint placeholders that were never patched,
- demo launch issues,
- Cog network download failures,
- and generation failures that are really data-shape problems.

## Handy reminders

- The runtime defaults in the source scripts use 512x512 generation space.
- Guidance scale and DDIM steps are part of the user-facing API; document them.
- The local demo is intentionally coarse-mask sensitive.
- A successful import check does not prove the generation path is ready.

## Cross-links

When the issue is actually about setup or checkpoints, route back to
`setup-and-checkpoints`.
When the issue is about dataset layout, route to `data-and-training`.

## Quality bar

A future agent should be able to answer generation and demo questions from this
branch alone, plus the bundled references and validation scripts, without
reopening the source repository.
