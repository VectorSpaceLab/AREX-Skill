---
name: image-preparation
description: "Prepare and validate DreamCraft3D reference images, sidecar maps,
  and preprocessing prerequisites."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Image Preparation

Use this sub-skill when a task is about getting a single reference image ready for DreamCraft3D: background removal, RGBA/depth/normal sidecars, recentering, caption sidecars, or diagnosing why `data.image_path` cannot be loaded.

## Read first

- Read [references/image-inputs.md](references/image-inputs.md) for the expected file layout, preprocessing workflow, CLI arguments, and how sidecars feed the stage configs.
- Read [references/troubleshooting.md](references/troubleshooting.md) when preprocessing or stage startup fails because images, sidecars, model checkpoints, CUDA, or optional captioning dependencies are missing.
- Run or adapt [scripts/validate_preprocessed_image.py](scripts/validate_preprocessed_image.py) when you need a safe sidecar check that does not import torch, run Omnidata, remove backgrounds, download models, or mutate the input image.

## When to use this sub-skill

Use it for requests like:

- "Prepare my image for DreamCraft3D."
- "Why does `single-image-datamodule` say it cannot find depth/normal?"
- "Check whether `mushroom_log_rgba.png` is ready for the configs."
- "Explain `preprocess_image.py --recenter` and output names."

## Workflow

1. Determine the intended input image stem. DreamCraft3D stage configs normally use an RGBA image path such as `load/images/mushroom_log_rgba.png`.
2. Check sidecars before launching training:
   - the RGBA input must exist and should have an alpha channel,
   - configs with `requires_depth: true` need a sibling `<stem>_depth.png`,
   - configs with `requires_normal: true` need a sibling `<stem>_normal.png`,
   - captions are optional and only created when captioning is requested.
3. If sidecars are missing, decide whether the user wants full preprocessing. Full preprocessing uses background removal, Omnidata depth/normal checkpoints, and CUDA by default; do not run it as a cheap validation step.
4. Route back to `generation-pipeline` only after the image path and required sidecars are ready or the limitation is explicitly documented.

## Safe validator

From a DreamCraft3D checkout, point the bundled validator at the intended RGBA file:

```bash
python <skill-dir>/sub-skills/image-preparation/scripts/validate_preprocessed_image.py \
  --image load/images/mushroom_log_rgba.png --require-depth --require-normal
```

Use `--json` for machine-readable output and `--allow-missing` when you want a non-failing report while planning fixes.

## Decision points

- If the user has a plain RGB/JPEG/PNG image, preprocessing is needed before the main stages.
- If the user already has `_rgba`, `_depth`, and `_normal` files, prefer validating sidecars over rerunning expensive models.
- If the task is about checkpoint chaining or launch commands, route to `generation-pipeline`.
- If the task is about Zero123++ multiview images or LoRA texture boosting, route to `bootstrapped-texture`.
- If the task is about mesh export or metrics, route to `export-and-evaluation`.
