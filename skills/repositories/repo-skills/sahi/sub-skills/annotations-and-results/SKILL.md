---
name: annotations-and-results
description: "Guide SAHI annotation, prediction result, mask, COCO export,
  optional conversion, visualization, and file helper objects."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# annotations-and-results

Use this sub-skill when a task is about SAHI's low-level data objects and result conversions: `BoundingBox`, `Category`, `Mask`, `ObjectAnnotation`, `PredictionScore`, `ObjectPrediction`, `PredictionResult`, COCO annotation/prediction dictionaries, optional FiftyOne or imantics conversion, visualization helpers, mask/bbox helpers, and lightweight file/import utilities.

Route away when the task owner is not object/result plumbing:

- Full prediction runs, detector setup, slicing parameters, batch prediction, CLI prediction, or video prediction: use `../sliced-inference/SKILL.md`.
- Full COCO dataset creation, slicing, remapping, evaluation, YOLO export, or dataset-scale FiftyOne workflows: use `../dataset-tools/SKILL.md`.
- NMS/NMM/GreedyNMM algorithm behavior or backend acceleration: use `../postprocess-backends/SKILL.md`.

## Start here

1. Read [objects and exports](references/objects-and-exports.md) before constructing or serializing annotation/prediction objects. It records constructor shapes, coordinate conventions, image-id handling, mask behavior, COCO JSON shapes, and optional FiftyOne/imantics conversions.
2. Read [CV and file helpers](references/cv-and-file-helpers.md) when converting masks, drawing predictions, reading images, listing files, saving JSON, checking imports, or debugging OpenCV/Pillow color assumptions.
3. Read [troubleshooting](references/troubleshooting.md) when boxes are invalid, category types fail, masks need `full_shape`, COCO masks disappear, optional conversion packages are missing, images load with wrong colors, or output paths are surprising.
4. For a dependency-light local sanity check, run `python scripts/prediction_objects_smoke.py` from this sub-skill directory. Add `--visualize` or `--write-json` only when you want temporary outputs.

## Minimal decision checklist

- Decide which coordinate format is entering SAHI: core objects use `[minx, miny, maxx, maxy]`; COCO bboxes use `[x, y, width, height]`.
- Keep image shapes as `[height, width]` for masks and `full_shape`; keep image IDs explicit when exporting per-image COCO predictions.
- Treat `fiftyone` and `imantics` as optional packages. Guard those conversions or give a fallback COCO JSON path.
- Use `PredictionResult.export_visuals` for simple PNG output; use lower-level visualization helpers when custom color or export format is required.
- Never let helper scripts download data, train models, require credentials, or write outside a caller-chosen or temporary output directory.
