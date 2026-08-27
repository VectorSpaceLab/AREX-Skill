---
name: data-preparation
description: "Guides Nerfstudio dataset conversion, transforms.json validation,
  camera conventions, device capture modes, and dataparser selection."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Data Preparation

Use this route before training when the task is about custom captures, camera
poses, `transforms.json`, `ns-process-data`, or choosing a dataparser.

## What this route covers

- Converting images, videos, Polycam, Record3D, Metashape, RealityCapture, ODM, and Project Aria style captures into the Nerfstudio dataset layout.
- Validating the Nerfstudio `transforms*.json` schema, image/depth/mask paths, split lists, and camera conventions.
- Distinguishing COLMAP/FFmpeg/hloc/external-tool requirements from package-level Python issues.
- Choosing between `nerfstudio-data`, `blender-data`, `minimal-parser`, `colmap`, and other built-in dataparser names.

## What this route excludes

- Training method choice and config overrides: use `training-and-configs` after the dataset validates.
- Dataset download commands: use `cli-workflows` first, because downloads need network and disk checks.
- Custom dataparser packaging: use `api-extension`.

## Read/run these bundled files

- [`references/data-formats.md`](references/data-formats.md) for `transforms*.json`, coordinate, depth, mask, and split fields.
- [`references/workflows.md`](references/workflows.md) for conversion recipes and dataparser routing.
- [`references/troubleshooting.md`](references/troubleshooting.md) for COLMAP, FFmpeg, path, and schema failures.
- [`scripts/validate_nerfstudio_dataset.py`](scripts/validate_nerfstudio_dataset.py) to check a dataset directory or `transforms*.json` without modifying data.

## Safe workflow

1. Identify the capture type and external prerequisites.
2. If using images/video, confirm COLMAP and FFmpeg unless an existing sparse model makes `--skip-colmap` valid.
3. Run the appropriate `ns-process-data` command into a new output directory.
4. Validate the output directory with the bundled validator.
5. Pass the dataset directory to `ns-train` through `training-and-configs`.

## Key reminders

- Nerfstudio uses OpenGL/Blender-style camera coordinates; COLMAP/OpenCV axes differ and are converted by the processing/dataparser code.
- Image paths in `transforms*.json` are relative to the dataset directory unless absolute paths are intentionally used.
- Depth images are specified per frame with `depth_file_path` and are interpreted in millimeters by default.
- Masks must be one-channel black/white images, same resolution as RGB, and must be present for all frames if used.
