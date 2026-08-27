---
name: inference
description: "Restore single images from DeblurGAN checkpoints and export HTML results."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# inference

Use this sub-skill when the task is to restore or inspect images with a trained DeblurGAN checkpoint.

## What this route covers

- Single-image inference with `model=test` and `dataset_mode=single`.
- Checkpoint lookup and result-directory layout.
- HTML output generation for restored images.
- CPU fallback for inference with `--gpu_ids -1`.
- A wrapper that avoids the source script's brittle external `ssim` import path.

## Read this when the user asks for

- A command to deblur one image folder with a trained checkpoint.
- Help finding `latest_net_G.pth` or choosing the right epoch label.
- A safe CPU inference command.
- A way to inspect or save the generated HTML results.

## Primary files

- `scripts/run_inference.py` — portable wrapper around the repository's test-time pipeline.
- `references/workflows.md` — command patterns, result paths, and CPU fallback notes.
- `references/troubleshooting.md` — checkpoint, import, and folder-layout failures.

## Workflow summary

1. Point the run at a folder of standalone images.
2. Choose the checkpoint directory and epoch label.
3. Use `model=test` with `dataset_mode=single` and, for headless runs, `--gpu_ids -1`.
4. Save the generated HTML and PNGs under the results directory.
5. If you want a smoke-style run, keep `how_many` small and use a tiny image folder.

## Decision points

- If the task is about building the dataset rather than restoring images, route back to data-preparation.
- If the task is about optimizing weights or resuming training, route to training.
- If the user wants the exact source `test.py` behavior, remember that the shipped script imports `ssim` directly; the wrapper avoids that brittle path.

## Important reminders

- The inference wrapper creates the checkpoint directory before the visualizer is constructed.
- The wrapper defaults to a headless-friendly display setting so the run does not depend on visdom.
- The repository's `TestModel` expects `single` dataset mode and a generator checkpoint with the requested epoch label.

## Cross-links

- Read the root installation reference if torch, torchvision, or the optional compatibility packages are missing.
- Read the root troubleshooting reference for checkpoint naming and source-script mismatches.
- Read the data-preparation sub-skill first if you still need to build the input image folder.
