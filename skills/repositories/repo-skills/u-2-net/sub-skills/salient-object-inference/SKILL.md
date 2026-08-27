---
name: salient-object-inference
description: "Run U-2-Net salient object and human segmentation inference from
  image folders to PNG masks with explicit weights and safe diagnostics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Salient Object Inference

Use this sub-skill when the user needs U-2-Net image-folder inference that writes PNG masks: generic salient object detection with `u2net` or `u2netp`, or human/person segmentation with a `u2net_human_seg.pth` checkpoint.

## Start here

1. Choose the task and matching checkpoint from [model weights](references/model-weights.md).
2. Run the bundled helper [`scripts/u2net_infer.py`](scripts/u2net_infer.py) instead of original demo scripts.
3. Use [workflows](references/workflows.md) for command recipes, preprocessing/output behavior, and validation checks.
4. Use [troubleshooting](references/troubleshooting.md) for missing weights, empty input folders, checkpoint mismatches, blank masks, NaNs, CUDA/device issues, and output naming surprises.

## Common routes

- **Fast CPU saliency on a custom image folder:** use `--task saliency --model u2netp --device cpu --weights ... --input-dir ... --output-dir ...`.
- **Full saliency model:** use `--task saliency --model u2net` and a `u2net.pth` checkpoint.
- **Human segmentation:** use `--task human` with `u2net_human_seg.pth`; human mode uses full `U2NET(3, 1)`, not `U2NETP`.
- **Plumbing-only smoke checks:** add `--allow-random-weights-for-smoke --max-images 1` only to verify imports, preprocessing, model forward, and mask writing. Do not present random-weight outputs as meaningful predictions.

## Boundaries

- Portrait generation, face cropping, drawing-style portrait prediction, and compositing belong to `portrait-workflows`.
- Training data layout, transforms for training, and retraining plans belong to `data-and-training`.
- Architecture internals, refactored builders, side-output semantics, and checkpoint-shape debugging belong to `model-architecture`.

## Minimal command shape

```bash
python scripts/u2net_infer.py \
  --task saliency \
  --model u2netp \
  --weights PATH_TO_WEIGHTS/u2netp.pth \
  --input-dir INPUT_IMAGES \
  --output-dir OUTPUT_MASKS \
  --device cpu
```

The helper writes one RGB PNG mask per input image using the input filename stem, resized back to the original image dimensions.
