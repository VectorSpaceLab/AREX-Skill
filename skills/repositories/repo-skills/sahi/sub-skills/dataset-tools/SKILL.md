---
name: dataset-tools
description: "Guide SAHI COCO dataset creation, slicing, filtering, conversion,
  evaluation, error analysis, and visualization workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Dataset Tools

Use this sub-skill when a task is about SAHI dataset operations rather than model
construction or per-image prediction. It covers COCO-style dataset creation,
loading, slicing, filtering, merging, train/validation splitting, YOLO export,
COCO evaluation/error analysis, and FiftyOne visualization.

## Route here for

- Building or loading COCO datasets with `Coco`, `CocoImage`,
  `CocoAnnotation`, `CocoPrediction`, and category definitions.
- Slicing a COCO dataset with `sahi.slicing.slice_coco` or `sahi coco slice`.
- Remapping/filtering categories, clipping boxes to image dimensions, keeping or
  dropping negative images, subsampling/upsampling, merging datasets, and
  train/validation splitting.
- Exporting COCO datasets to YOLO/Ultralytics layout with `sahi coco yolo` or
  the `Coco` export helpers.
- Running COCO evaluation, error-analysis plots, or FiftyOne visualization when
  optional dependencies are available.

## Route away

- Per-image prediction, sliced inference, model loading, or detector backend
  setup: use the sliced-inference and model-integrations sibling sub-skills.
- Low-level conversion between SAHI prediction/result objects and annotation
  objects: use the annotations-and-results sibling sub-skill.

## Operating references

1. Read [COCO CLI and API](references/coco-cli-and-api.md) for SAHI dataset APIs,
   CLI commands, required optional dependencies, and workflow recipes.
2. Read [Data formats and output layouts](references/data-formats.md) before
   writing or consuming COCO JSON, sliced datasets, YOLO exports, COCO result
   JSON, evaluation outputs, or FiftyOne inputs.
3. Read [Troubleshooting](references/troubleshooting.md) when loading fails,
   categories do not match, negative samples disappear, boxes are clipped or
   invalid, evaluation dependencies are missing, FiftyOne does not launch, or
   YOLO symlinks fail.
4. For a dependency-light local sanity check, run
   `python scripts/coco_fixture_smoke.py` from this sub-skill directory. The
   script creates only temporary files and does not require `pycocotools`,
   FiftyOne, network access, model weights, or training.

## Minimal decision checklist

- Confirm whether the task needs API usage, CLI usage, or both.
- Confirm the image directory that `images[*].file_name` resolves against.
- Decide whether images without annotations must be preserved
  (`ignore_negative_samples=False`) or excluded.
- Decide whether category IDs must be remapped before splitting or YOLO export.
- Treat `pycocotools` and FiftyOne as optional: guard those workflows and provide
  a fallback JSON validation path when they are unavailable.
