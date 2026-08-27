---
name: visualization-and-export
description: "Guides Nerfstudio viewer, evaluation, rendering, camera-path,
  point-cloud, mesh, camera, and Gaussian Splat export workflows from saved
  config.yml artifacts."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Visualization and Export

Use this route after a run has a saved `config.yml`, or when the task asks for
viewer, metrics, rendering, point clouds, meshes, camera poses, or Gaussian
Splat exports.

## What this route covers

- `ns-viewer --load-config CONFIG.yml` for visualizing a completed run.
- `ns-eval --load-config CONFIG.yml --output-path metrics.json` for average metrics and optional render outputs.
- `ns-render` camera path, spiral/interpolated, or dataset rendering command planning.
- `ns-export` subcommands: `pointcloud`, `tsdf`, `poisson`, `marching-cubes`, `cameras`, and `gaussian-splat`.
- Preflight checks for config paths, output locations, remote viewer ports, checkpoint artifacts, normal/depth/RGB output names, and GPU/memory risk.

## What this route excludes

- Data conversion and `transforms.json` validation: use `data-preparation`.
- Training command construction and resume behavior: use `training-and-configs`.
- Custom model/dataparser packaging: use `api-extension`.

## Read/run these bundled files

- [`references/workflows.md`](references/workflows.md) for viewer/eval/render/export command recipes.
- [`references/api-reference.md`](references/api-reference.md) for relevant Python classes and functions.
- [`references/troubleshooting.md`](references/troubleshooting.md) for viewer, checkpoint, metric, export, and memory failures.
- [`scripts/check_artifacts.py`](scripts/check_artifacts.py) to validate config/output path readiness without loading a model.
- [`scripts/check_viewer_config.py`](scripts/check_viewer_config.py) to preflight viewer ports and config paths without starting the service.

## Safe workflow

1. Locate the saved `config.yml` from the completed run.
2. Verify that referenced checkpoint and dataset artifacts still exist.
3. Choose the output action: viewer, eval, render, or export.
4. Preflight paths and ports using bundled scripts.
5. Run the selected command only after confirming GPU/memory/time and output directory expectations.
