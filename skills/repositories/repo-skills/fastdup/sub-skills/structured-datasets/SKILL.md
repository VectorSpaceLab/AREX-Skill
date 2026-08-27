---
name: structured-datasets
description: "Guide fastdup workflows for labeled image datasets, object
  detection annotations, dataset-source loaders, and export helpers."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# structured-datasets

Use this sub-skill when the workflow already has labels, splits, bounding boxes, or a notebook-guided dataset-source example.

## Use when

The request mentions any of the following:

- image classification datasets with labels or train/test splits
- object detection datasets with COCO-style or bbox annotations
- annotation dataframes with `filename`, `label`, `split`, or bbox columns
- notebook-guided source examples for Hugging Face, Kaggle, Roboflow, Labelbox, TensorFlow Datasets, or Torchvision
- CVAT or LabelImg export helpers
- `read_coco_labels`, `fd.run(annotations=...)`, or labeled gallery workflows

## Typical workflow

1. Decide whether the input is a dataframe, a source adapter, or a generated fixture.
2. Normalize the dataframe columns before the run.
3. For object detection, keep the bbox columns consistent and choose `data_type="bbox"` when needed.
4. Run `fd.run(annotations=...)` and inspect the label-aware galleries.
5. Export to external tools only after the fastdup run succeeds.

## What to read

- `../../references/api-reference.md` for the `fd.run(...)` and gallery entry points
- `../../references/data-formats.md` for annotation schemas and export-oriented outputs
- `../../references/workflows.md` for the labeled-data workflow family
- `../../references/source-loaders.md` for notebook-based dataset-source examples and their failure modes
- `../../references/exports.md` for CVAT and LabelImg handoff details
- `references/troubleshooting.md` in this sub-skill for annotation and loader-specific issues
- `../../references/troubleshooting.md` for package and platform-wide failures

## Bundled scripts

Run these for reproducible local smoke checks:

- `../../scripts/make_synthetic_bbox_data.py` — create a tiny bbox fixture and matching annotation tables
- `../../scripts/run_labeled_classification_smoke.py` — exercise the labeled image workflow on synthetic data
- `../../scripts/run_labeled_detection_smoke.py` — exercise the bbox workflow on synthetic data

## Common decisions

- Prefer manual annotation dataframes for the most reliable path.
- Make sure the annotation dataframe matches the input folder layout.
- Use absolute filenames when the matching logic is ambiguous.
- For bbox work, preserve the coordinate column names expected by fastdup.
- Treat source-specific loaders as optional conveniences; they are not required for the core labeled-data workflow.
- Prefer the manual dataframe path when a source package, cache, or credentialed download is unstable.

## Known limitation

The convenience Hugging Face dataset wrapper is currently fragile in the inspected release line and may fail during import. If it fails, fall back to a manually built dataframe rather than blocking the task.
