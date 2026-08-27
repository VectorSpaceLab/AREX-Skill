---
name: visualization-and-extensions
description: "Guides Open3D-ML visualization, bounding boxes, TensorBoard
  summaries, and optional OpenVINO wrapping."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Visualization and Extensions

Use this sub-skill when you want to inspect point clouds, compare labels or
predictions, generate TensorBoard 3D summaries, or understand the optional
OpenVINO wrapper path.

## What this sub-skill covers

- `Visualizer` usage for datasets and custom point clouds.
- Label lookup tables and bounding-box rendering.
- Prediction/comparison visualization.
- TensorBoard 3D summary field conventions.
- Optional OpenVINO wrapper guidance for supported models.
- Headless and GUI-safe troubleshooting.

## When to route here

- "How do I visualize a point cloud with labels or predictions?"
- "How do I draw 3D bounding boxes?"
- "How do I write Open3D-ML data into TensorBoard?"
- "How do I use the OpenVINO wrapper?"
- "Why does the visualizer fail on this machine?"

## Use the bundled helper

Run `scripts/create_visualization_fixture.py` to generate a tiny point-cloud,
label, prediction, and bounding-box fixture without opening a GUI or downloading
demo data.

## Reading order

1. Read `references/api-reference.md` for the verified visualization API and
   data-shape facts.
2. Read `references/workflows.md` for dataset, custom-data, TensorBoard, and
   OpenVINO recipes.
3. Read `references/troubleshooting.md` when GUI or backend-specific issues
   occur.

## Boundary notes

Include:
- Dataset and custom-data visualization.
- Bounding boxes and label LUTs.
- TensorBoard 3D summaries.
- Optional OpenVINO wrapper guidance.

Exclude:
- Training loops and registry details; use `training-and-pipelines`.
- Dataset folder layout and split validation; use `datasets-and-preprocessing`.
- Generic install/backend checks; use `install-and-inspect`.

## Minimal workflow

1. Build or load a point-cloud fixture.
2. Choose a LUT or box list if you need labels or 3D boxes.
3. Use the visualizer or TensorBoard summary path that matches the task.
4. Fall back to the fixture helper or summary writer when GUI is unavailable.

## Good handoff signals

A future agent should be able to answer these from this sub-skill alone:

- Which keys belong in a point-cloud visualization dictionary.
- How to write 3D summaries with the documented `vertex_*` fields.
- Which models are supported by the OpenVINO wrapper.
- What to do when GUI rendering is unavailable.
