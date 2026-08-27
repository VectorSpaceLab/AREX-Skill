---
name: inference-and-export
description: "Run zi2zi checkpoint inference, style interpolation, transition
  GIF planning, and generator-only export from legacy TensorFlow 1.x
  checkpoints."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# zi2zi inference and export

Use this sub-skill when a task is about generating glyphs from a trained zi2zi
checkpoint, interpolating between style labels, creating frame sequences or a
GIF, or exporting generator-only variables for later reuse. It does not launch
long inference jobs automatically; it explains the checkpoint contract and
prints safe command templates.

## Use this sub-skill when

- The user has a checkpoint directory and wants generated glyphs.
- The task mentions `infer.py`, `export.py`, `model_dir`, `source_obj`,
  `embedding_ids`, `interpolate`, `steps`, `output_gif`, `uroboros`, or exported
  generator weights.
- The user wants to know how inference chooses between single-style generation
  and random style selection.
- The user needs to diagnose checkpoint restore failures, output-image naming,
  or interpolation problems.

## Route elsewhere

- Data rendering and `.obj` packaging go to
  [data-preparation](../data-preparation/SKILL.md).
- Training, fine-tuning, or label shuffling go to
  [training-and-model](../training-and-model/SKILL.md).
- Compatibility questions go to the root [compatibility](../../references/compatibility.md)
  reference.

## Core inference facts

- `infer.py` restores generator variables from a checkpoint and uses a source
  object file to provide images.
- If `embedding_ids` contains one integer, the model uses that style for every
  source image. If it contains multiple IDs, the script picks randomly from the
  list for each batch.
- `interpolate=1` asks the model to linearly interpolate between style vectors.
  With `uroboros=1`, the interpolation path closes the loop by appending the
  first ID to the end of the chain.
- `output_gif` triggers GIF compilation from the rendered interpolation frames.
- `export.py` saves generator-only variables, which include the embedding table
  and generator weights.

## Output conventions

- Normal inference writes files named `inferred_%04d.png` in the save directory.
- Interpolation writes `frame_<src>_<dst>_step_<idx>.png` files.
- GIF compilation expects those frame PNGs in the save directory and writes the
  named GIF beside them.
- Export uses TensorFlow checkpoint naming with a generator model prefix.

## Recommended workflow

1. Verify the checkpoint directory contains a TensorFlow checkpoint state.
2. Decide whether you want one style ID, a random mix, or interpolation between
   two or more style IDs.
3. Confirm the source object file contains paired glyph records and that its
   batch size is compatible with the inference command.
4. Use the command planner to validate flags and paths before launching any
   long job.
5. Inspect outputs after the first few batches, especially if the chosen style
   labels or batch size do not match the training run.

Read [inference-workflow.md](references/inference-workflow.md) for command
shapes and evaluation steps. Read [checkpoints-and-outputs.md](references/checkpoints-and-outputs.md)
for restore/export expectations and filename conventions. Read [troubleshooting.md](references/troubleshooting.md)
for checkpoint, batch-size, GIF, and source-object failures.

## Bundled helper

- [scripts/plan_zi2zi_inference.py](scripts/plan_zi2zi_inference.py) validates
  inference, interpolation, and export arguments and prints the command that a
  future agent should run in a legacy zi2zi environment.

## What not to promise automatically

- Do not promise restoration of a checkpoint without checking that the concrete
  checkpoint files exist and match the chosen hyperparameters.
- Do not promise a successful interpolation run unless `embedding_ids` contains
  at least two integers.
- Do not promise export success if the model directory contains only partial or
  mismatched checkpoint shards.
