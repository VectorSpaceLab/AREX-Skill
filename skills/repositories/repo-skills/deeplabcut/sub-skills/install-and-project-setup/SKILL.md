---
name: install-and-project-setup
description: "Install DeepLabCut, launch the GUI or lite mode, create and
  inspect projects, and summarize project layouts safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: LGPL 3.0
---

# install-and-project-setup

Use this sub-skill when the task is about installation choices, launcher behavior, project creation, adding videos, or safe inspection of a DeepLabCut project.

## Use this sub-skill for
- choosing a DeepLabCut install flavor or backend
- checking whether `dlc` or `python -m deeplabcut` opens the GUI or prints the lite notice
- creating a standard, multi-animal, or 3D project
- adding videos to an existing project
- inspecting `config.yaml` and the project tree without writing files

## Route elsewhere
- Frame extraction, labeling, and training-dataset creation → `data-labeling-and-training-datasets`
- Training, evaluation, analysis, and export → `pytorch-training-evaluation-inference`
- Tracking, stitching, and re-identification → `multi-animal-tracking`
- Filtering, outlier refinement, labeled videos, trajectories, and 3D post-processing → `postprocessing-3d-video-exports`

## Key facts
- Supported Python is 3.10–3.12.
- The installed console script is `dlc`, which points to `deeplabcut.__main__:main`.
- `python -m deeplabcut` follows the same launch path.
- If GUI dependencies are present, the launcher opens the GUI; if `PySide6` is missing, it prints the lite notice instead.
- `deeplabcut.cli` exposes a click command group for command discovery, but it is not the console entry point.
- Project setup APIs:
  - `deeplabcut.create_new_project(project, experimenter, videos, working_directory=None, copy_videos=False, video_extensions=None, multianimal=False, individuals=None)`
  - `deeplabcut.add_new_videos(config, videos, copy_videos=False, coords=None, extract_frames=False)`
  - `deeplabcut.create_new_project_3d(project, experimenter, num_cameras=2, working_directory=None)`

## Bundled references
- `references/project-workflows.md`
- `references/configuration.md`
- `references/troubleshooting.md`

## Bundled script
- `scripts/summarize_dlc_project.py`

## Keep the routing narrow
Stop at project setup and inspection. Do not continue into frame extraction, labeling, training, tracking, filtering, or 3D calibration beyond what is needed to create or summarize the project skeleton.
