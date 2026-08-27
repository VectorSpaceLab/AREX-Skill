---
name: data-preparation
description: "Guides gaussian-splatting scene layout checks, COLMAP/Blender
  conversion, and depth-regularization preparation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Data Preparation

Use this sub-skill when the task is about turning raw images or existing SfM outputs into the scene layouts that `train.py`, `render.py`, and `metrics.py` expect.

## Read First

- Read [references/data-formats.md](references/data-formats.md) for the required COLMAP, Blender/NeRF synthetic, depth, and model-output folder layouts.
- Read [references/conversion-workflows.md](references/conversion-workflows.md) when the user wants COLMAP/ImageMagick conversion commands or a scene layout preflight.
- Read [references/troubleshooting.md](references/troubleshooting.md) for camera model, depth, COLMAP, and external command failures.
- Run [scripts/validate_scene_layout.py](scripts/validate_scene_layout.py) before building any training/rendering command that depends on scene structure.
- Run [scripts/make_depth_scale.py](scripts/make_depth_scale.py) when the user needs `depth_params.json` for depth regularization. It uses the bundled [scripts/read_write_model.py](scripts/read_write_model.py) parser support file.

## What This Sub-Skill Covers

- Raw image to COLMAP scene preparation.
- Validation of `images/`, `sparse/0/`, `transforms_train.json`, `transforms_test.json`, and model output directories.
- Recognition of supported camera models and when undistorted PINHOLE/SIMPLE_PINHOLE data is required.
- Depth-regularization support files and `-d/--depths` folder layout.
- Safe command construction for conversion and depth-prep tasks.

## What This Sub-Skill Excludes

- Optimizer selection, iteration schedules, and training command construction. Route those to [../training/SKILL.md](../training/SKILL.md).
- Offline rendering and metric computation. Route those to [../rendering-evaluation/SKILL.md](../rendering-evaluation/SKILL.md).
- SIBR viewer build/run details. Route those to [../viewers/SKILL.md](../viewers/SKILL.md).
- CUDA compiler or PyTorch installation. Route those to [../setup-and-backends/SKILL.md](../setup-and-backends/SKILL.md).

## Common Use Cases

1. A raw image folder and a COLMAP executable are available, and you need to know the right conversion command.
2. A user has a COLMAP scene but training fails because `sparse/0` or `images/` is missing.
3. A user wants depth regularization and needs `depth_params.json` generated from COLMAP plus per-image depth PNGs.
4. A user is unsure whether a dataset is Blender/NeRF synthetic or COLMAP and wants a structural check before training.

## Output Expectations

The sub-skill should help a future agent answer:

- What layout does this scene need?
- Which conversion command should be used?
- Why does training complain about the dataset or depth files?
- Which validator should be run before starting `train.py`?

