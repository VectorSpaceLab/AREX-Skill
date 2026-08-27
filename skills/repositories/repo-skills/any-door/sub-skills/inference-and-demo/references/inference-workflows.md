# Inference Workflows

This reference covers the two generation flows that show up most often in user
requests: single-image customization and VITON-HD-style batch generation.

## Single-image workflow

The source inference entry builds an item with:

- a masked reference image,
- a cropped target image,
- a collage / control tensor,
- crop metadata,
- and the output image reconstructed back into the target canvas.

Key runtime ideas:

- Reference and target masks are converted to bounding boxes first.
- The reference object is background-stripped and padded before resizing to the
  conditioning size.
- The target image is cropped around the target mask and then padded to square.
- The generation model uses a control tensor plus cross-attention conditioning.
- The final sample is pasted back into the target image region.

## Practical parameters

The source defaults show the most useful user-facing knobs:

- `guidance_scale`: controls how strongly the model follows the conditioning.
- `ddim_steps`: more steps generally means slower but potentially cleaner output.
- `strength`: scales the control branch.
- `seed`: keeps the run reproducible when the surrounding environment allows it.
- `enable_shape_control`: whether the target mask should guide the shape path.

## VITON-HD-style batch workflow

The repo’s batch example loops over a dataset directory, loads cloth and image
pairs, derives the masks from the dataset layout, and writes a per-image result.
This is useful when the user asks for “the same thing, but over a dataset”
or wants a VITON-HD test run.

## Suggested execution order

1. Patch the checkpoint placeholders.
2. Validate the reference/background masks.
3. Confirm the target crop assumptions.
4. Run the generation command or demo launch.
5. If the output is wrong, inspect the mask size and bounding-box logic before
   changing prompts or hyperparameters.

## What to preserve in explanations

- The output is mask-driven rather than prompt-driven.
- The generation canvas is 512x512 in the source workflow.
- The reference object is resized independently of the target canvas.
- The final result is pasted back into the target image rather than returned as
  a standalone crop.
