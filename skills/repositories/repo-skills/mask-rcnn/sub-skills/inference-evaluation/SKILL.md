---
name: inference-evaluation
description: "Routes Mask_RCNN inference, visualization, color splash, COCO
  evaluation, and nucleus RLE submission tasks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Inference, Visualization, and Evaluation

Use this sub-skill when a task asks how to run Mask_RCNN inference, inspect masks/boxes, produce color splash outputs, compute COCO metrics, or encode nucleus submissions.

## Read first by need

- Read [inference-workflows.md](references/inference-workflows.md) for `MaskRCNN(mode="inference")`, `detect()`, and postprocessing flow.
- Read [evaluation-and-visualization.md](references/evaluation-and-visualization.md) for display helpers, COCO result formatting, AP, and nucleus RLE details.
- Read [troubleshooting.md](references/troubleshooting.md) for empty predictions, image-shape mismatches, and encoding mistakes.
- Use [scripts/apply_color_splash.py](scripts/apply_color_splash.py) for a safe standalone splash postprocessor.
- Use [scripts/rle_tools.py](scripts/rle_tools.py) to inspect or convert nucleus-style RLE strings without the original notebook.

## Inference workflow

1. Build an inference config that usually sets `GPU_COUNT = 1`, `IMAGES_PER_GPU = 1`, and `DETECTION_MIN_CONFIDENCE = 0` for inspection work.
2. Load weights.
3. Call `model.detect([image])` where the list length matches `BATCH_SIZE`.
4. Inspect the returned dictionary keys: `rois`, `class_ids`, `scores`, and `masks`.
5. Route visualization to `mrcnn.visualize.display_instances` or the bundled splash/RLE helpers.
6. For evaluation, use the dataset-specific converter or the COCO AP helpers in the references.

## Boundary notes

- Dataset class loading and layout checks belong to [data-preparation](../data-preparation/SKILL.md).
- Training schedules and weight selection belong to [training](../training/SKILL.md).
- API signatures and graph-build compatibility belong to [core-apis](../core-apis/SKILL.md).
