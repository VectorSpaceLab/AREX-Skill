# Project workflows

## Install choices
DeepLabCut 3.x defaults to the PyTorch engine. Choose the lightest install that still covers the task:

- `deeplabcut` for core, headless use
- `deeplabcut[gui]` when the Project Manager GUI is needed
- `deeplabcut[modelzoo]` only when pretrained model-zoo or SuperAnimal workflows are needed later
- `deeplabcut[tf]` or a CUDA-specific TensorFlow extra only when the legacy TensorFlow engine is explicitly required

The supported Python range is 3.10–3.12.

## Launch behavior
- `dlc` and `python -m deeplabcut` follow the same launcher path.
- If GUI dependencies are installed, the launcher opens the GUI.
- If `PySide6` is missing, the launcher prints the lite notice instead of opening the GUI.
- `deeplabcut.cli` exposes a click command group for command discovery and routing, but it is not the installed console entry point.

## API signatures
```python
deeplabcut.create_new_project(
    project,
    experimenter,
    videos,
    working_directory=None,
    copy_videos=False,
    video_extensions=None,
    multianimal=False,
    individuals=None,
)

deeplabcut.add_new_videos(
    config,
    videos,
    copy_videos=False,
    coords=None,
    extract_frames=False,
)

deeplabcut.create_new_project_3d(
    project,
    experimenter,
    num_cameras=2,
    working_directory=None,
)
```

## Standard project setup
`create_new_project` creates a project directory named from the project, scorer, and date. If `working_directory` is omitted, the current directory is used.

Inputs can be:
- a list of video files
- a list of directories containing videos
- a mix of both

If directory paths are used, `video_extensions` controls which files are collected. The function writes a `config.yaml`, a `videos/` tree, a `labeled-data/` tree, a `training-datasets/` tree, and the project model folders that grow as later workflow steps run.

Behavior notes:
- API default: `copy_videos=False`
- CLI default: copy videos unless the user disables copying
- On Windows, symlink creation may require an elevated shell
- If symlinks fail, DeepLabCut may fall back to copying the videos
- If no valid videos are found, the function can return `nothingcreated`

The project tree should be expected to grow like this over time:

```text
project/
  config.yaml
  videos/
  labeled-data/
  training-datasets/
  dlc-models/
  dlc-models-pytorch/
```

A fresh project may not have every engine-specific folder yet. The PyTorch model tree usually appears once the first PyTorch shuffle or training artifact is created.

## Multi-animal project setup
Use `multianimal=True` when the project should follow the multi-animal workflow.

Key rules:
- `individuals` names should be explicit and consistent.
- `identity=True` only when the same individual can be recognized consistently across frames.
- `bodyparts` becomes the sentinel `MULTI!` in the multi-animal template; the actual shared points go in `multianimalbodyparts`.
- `uniquebodyparts` holds landmarks or objects that appear only once per frame.

Multi-animal projects use the same core project tree, but the config has additional fields for individuals, identity, and shared body parts.

## Adding videos later
`add_new_videos` updates an existing project’s `video_sets` list.

Use it when:
- new videos arrive after project creation
- crops need to be recorded per video
- the project should stay centered on the same config file

Notes:
- `coords` can override per-video crop bounds
- `extract_frames=True` hands off to the frame-extraction workflow, which belongs to a different sub-skill
- the function still writes the updated video list into the project config when used normally

## 3D project setup
`create_new_project_3d` creates the skeleton for a stereo 3D project.

Default assumptions:
- `num_cameras=2`
- the project is built around paired camera views
- camera names must stay stable after setup

Expected 3D project root shape:

```text
project-3d/
  config.yaml
  calibration_images/
  camera_matrix/
  corners/
  undistortion/
```

The 3D config stores the 3D scorer name, camera names, and per-camera references to the 2D projects that will be used later. Calibration and triangulation are not handled here; they are routed to the downstream 3D/post-processing sub-skill.

## Safe inspection with the bundled script
Use `scripts/summarize_dlc_project.py` to inspect either a project root or a `config.yaml`.

The script is read-only and reports:
- project metadata from the config
- whether the stored `project_path` matches the actual project root
- top-level folder presence
- a bounded sample of `video_sets`
- 3D camera metadata when present

It never writes to the project.
