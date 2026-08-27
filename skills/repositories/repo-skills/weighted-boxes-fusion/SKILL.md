---
name: weighted-boxes-fusion
description: "Route Weighted-Boxes-Fusion tasks for 2D box ensembling, 1D span
  fusion, and 3D cuboid fusion with ensemble_boxes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Weighted Boxes Fusion

Use this repo skill when a task asks you to merge predictions from multiple models with the `ensemble_boxes` package. The package covers three distinct geometry families:

- 2D detector boxes with WBF, NMS, Soft-NMS, and non-maximum weighted suppression.
- 1D spans or token intervals for NLP/NER-style fusion.
- 3D axis-aligned cuboids for volumetric or LiDAR-style detection.

The skill is split into focused sub-skills so future agents can route quickly by geometry and failure mode.

## Install and verify

Install the public package from PyPI:

```bash
python -m pip install ensemble-boxes
```

The bundled smoke helper uses only the package's runtime dependencies; no benchmark data, GUI extras, or detector checkpoints are required.

Then run the root smoke helper:

```bash
python scripts/check_install.py --case all
```

That script imports `ensemble_boxes` and exercises tiny 2D, 1D, and 3D in-memory cases without downloading data or opening GUI windows.

## Route map

### `sub-skills/box-ensembling/`
Use this for 2D normalized boxes in `[x1, y1, x2, y2]` order.

Choose it for tasks like:

- merging YOLO, Faster R-CNN, DetectoRS, or other detector outputs;
- choosing between `weighted_boxes_fusion`, `weighted_boxes_fusion_experimental`, `non_maximum_weighted`, `nms`, `soft_nms`, and `nms_method`;
- tuning `iou_thr`, `skip_box_thr`, `weights`, `conf_type`, `allows_overflow`, `sigma`, or `thresh`;
- explaining clipped coordinates, swapped corners, zero-area boxes, or score inflation.

Read:
- `sub-skills/box-ensembling/references/api-reference.md`
- `sub-skills/box-ensembling/references/workflows.md`
- `sub-skills/box-ensembling/references/troubleshooting.md`
- `sub-skills/box-ensembling/scripts/smoke_2d_ensembling.py`

### `sub-skills/line-segment-fusion/`
Use this for normalized 1D spans in `[x1, x2]` order.

Choose it for tasks like:

- fusing token spans or `predictionstring` intervals from several NLP models;
- mapping string classes to numeric labels before fusion and back afterward;
- tuning `iou_thr`, `skip_box_thr`, `weights`, `conf_type`, or `allows_overflow` for span ensembling.

Read:
- `sub-skills/line-segment-fusion/references/api-reference.md`
- `sub-skills/line-segment-fusion/references/workflows.md`
- `sub-skills/line-segment-fusion/references/troubleshooting.md`
- `sub-skills/line-segment-fusion/scripts/smoke_1d_fusion.py`

### `sub-skills/three-d-box-fusion/`
Use this for normalized 3D cuboids in `[x1, y1, z1, x2, y2, z2]` order.

Choose it for tasks like:

- fusing LiDAR, medical, or other volumetric detector outputs;
- choosing between `conf_type='avg'` and `conf_type='max'`;
- diagnosing axis-order mistakes, zero-volume boxes, or normalization problems.

Read:
- `sub-skills/three-d-box-fusion/references/api-reference.md`
- `sub-skills/three-d-box-fusion/references/workflows.md`
- `sub-skills/three-d-box-fusion/references/troubleshooting.md`
- `sub-skills/three-d-box-fusion/scripts/smoke_3d_fusion.py`

## Shared guidance

- Keep all geometry inputs normalized unless a sub-skill explicitly shows the normalization step.
- Keep one outer list entry per model, even when a model has no predictions.
- If the task asks about benchmark reproduction, read `references/benchmark-notes.md` first. Those scripts need external data and optional packages, so they are not part of the default smoke path.
- If import or installation fails, start with `references/troubleshooting.md` before guessing at geometry bugs.
- If the skill seems stale for the current checkout, read `references/repo-provenance.md` and refresh the skill instead of reusing it blindly.
- For router integration metadata, consult `references/repo-routing-metadata.json`.

## Minimal runtime check

The fastest package check is:

```bash
python -c "from ensemble_boxes import weighted_boxes_fusion; print(weighted_boxes_fusion)"
```

For a broader smoke, use `scripts/check_install.py --case all`.

## What not to expect

- No training loop, model zoo, or detector architecture guidance.
- No built-in GUI visualization requirement.
- No default benchmark downloads.
- No GPU dependency for the package APIs covered here.
