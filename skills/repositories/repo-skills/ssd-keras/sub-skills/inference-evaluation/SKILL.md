---
name: inference-evaluation
description: "Route for SSD Keras inference, decoding, visualization, and evaluation."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Inference and Evaluation

Use this route when the task is about loading a trained SSD model, decoding detections, visualizing boxes, or measuring performance on VOC / COCO-style data.

## What this route covers

- building inference or inference-fast models
- loading saved SSD models with custom objects
- decoding raw predictions
- interpreting or visualizing boxes on images
- computing VOC-style average precision and mean AP
- exporting COCO predictions to JSON
- remapping predictions back to the original image frame after transforms

## What this route excludes

- training loops
- class-count adaptation and weight sampling
- low-level dataset parsing details beyond what evaluation needs

Send those tasks to `training` or `data-preparation`.

## First things to check

1. Open `references/model-architecture.md` to confirm the decode / model-mode contract.
2. Open `references/data-formats.md` if the evaluation data needs a parser or category mapping.
3. Open `references/workflows.md` for the notebook-derived inference and evaluation steps.
4. Run `scripts/smoke.py` for a tiny synthetic decode and evaluation check.

## Typical workflow

### 1. Load the model

- Build the model in `inference` or `inference_fast` mode when you want the decoder inside the graph.
- Load a saved model with the custom layers in `custom_objects`.
- If you only have raw predictions, decode them with the NumPy helpers instead of rebuilding the graph.

### 2. Prepare images

- Resize and convert channels with the same image-size assumptions used during training.
- Use `DataGenerator` plus inverse transforms when predictions need to be mapped back to the original image coordinates.

### 3. Decode and filter predictions

- Use `decode_detections` when you want the original per-class NMS behavior.
- Use `decode_detections_fast` when a faster global-NMS path is acceptable.
- Keep an eye on `confidence_thresh`, `iou_threshold`, `top_k`, and `normalize_coords` when the output looks empty or shifted.

### 4. Evaluate

- Use `Evaluator` for VOC-style metrics.
- Choose the AP mode that matches the benchmark you want to reproduce.
- For COCO-style export, first build the category map and then write the predictions to JSON.

## Useful source objects

- `ssd_300`
- `ssd_512`
- `build_model`
- `DecodeDetections`
- `DecodeDetectionsFast`
- `decode_detections`
- `decode_detections_fast`
- `Evaluator`
- `get_coco_category_maps`
- `predict_all_to_json`
- `apply_inverse_transforms`

## Script path

- `scripts/smoke.py` — builds a tiny inference model, decodes a synthetic prediction, and runs a toy evaluator / COCO-export check.

## Quick decision guide

- Need per-class average precision or mean AP? Use `Evaluator`.
- Need a JSON file for COCO evaluation? Use `predict_all_to_json`.
- Need a simple confidence-thresholded box list? Use `decode_detections` or `decode_detections_fast`.
