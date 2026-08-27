# Setup and Checkpoint Checklist

Use this checklist when a user needs a clean setup or reports a missing model.

## Checklist

- Confirm the repo root is the AnyDoor checkout, not a nested example or data directory.
- Confirm `cldm/`, `ldm/`, `datasets/`, `configs/`, `dinov2/`, and `iseg/` are visible.
- Confirm the environment checker reports torch, CUDA, and the key imports.
- Replace the placeholder AnyDoor checkpoint in `configs/inference.yaml`.
- Replace the placeholder AnyDoor checkpoint in `configs/demo.yaml`.
- Replace the DINOv2 weight placeholder in `configs/anydoor.yaml`.
- If the demo’s interactive segmentation toggle is enabled, confirm the optional
  mask-refinement weight exists.
- If xformers is absent, record it as optional rather than blocking.

## Config fields to remember

- `configs/inference.yaml: pretrained_model`
- `configs/demo.yaml: pretrained_model`
- `configs/anydoor.yaml: model.params.cond_stage_config.weight`

## What good looks like

- The config patcher has no remaining placeholder replacements.
- The environment checker can import the core modules.
- CUDA is visible when generation is expected.
- The user can name the concrete checkpoint files that will be used later by
  inference or demo workflows.
