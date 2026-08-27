# Tracking and Evaluation Workflows

## When to read

Read this when a task asks to run a PyTracking tracker on a dataset sequence, a full benchmark dataset, a video file, a webcam stream, or an experiment function. Use the bundled `../scripts/build_tracking_command.py` helper to build commands safely before launching any side-effecting run.

## Execution prerequisites

- A PyTracking checkout or installed source tree in the target environment, with both `pytracking` and `ltr` importable.
- A CUDA-capable PyTorch environment for realistic pretrained network trackers. CPU-only checks can validate command shape and configuration but do not prove full tracker runtime.
- `pytracking/evaluation/local.py` in the target checkout with `network_path`, `results_path`, `segmentation_path`, and dataset-specific paths set.
- The requested pretrained tracker checkpoint in the configured network path. Tracker parameter files often load checkpoint filenames internally.
- Dataset/video/webcam/GUI resources and enough runtime budget before executing a command.

## Build a dataset or sequence command

Use the helper to emit a copyable command without running it:

```bash
python scripts/build_tracking_command.py dataset --tracker dimp --param dimp50 --dataset otb --sequence Soccer --debug 0 --explain
```

The emitted command follows the upstream shape:

```bash
python pytracking/run_tracker.py dimp dimp50 --dataset_name otb --sequence Soccer --debug 0 --threads 0
```

Key decisions:

- `--tracker` is the directory/import name under the tracker family, e.g. `atom`, `dimp`, `eco`, `keep_track`, `kys`, `lwl`, `rts`, `tamos`, `tomp`.
- `--param` is the parameter module basename for that tracker, e.g. `dimp50`, `prdimp50`, `default`, `tamos_resnet50`.
- `--dataset` must be one of the aliases in [datasets and results](datasets-and-results.md).
- Omit `--sequence` only when you intentionally want a full dataset run.
- Use `--threads 0` for sequential execution and easier debugging; raise it only after confirming data paths and memory.
- `--runid` changes output directories by appending a zero-padded run suffix in PyTracking's result layout.

## Build a video command

```bash
python scripts/build_tracking_command.py video --tracker atom --param default --videofile /data/video.mp4 --optional-box 100 80 60 40 --debug 0 --explain
```

The optional box is `x y width height`. If omitted, the OpenCV UI prompts for interactive target selection. `--save-results` asks the native script to write bounding boxes under the configured result path, so use it only when the output location is known.

## Build a webcam command

```bash
python scripts/build_tracking_command.py webcam --tracker dimp --param dimp50 --debug 0 --visdom off --explain
```

Webcam mode opens camera index 0 and an OpenCV window. It supports multiple target selections in the UI. Do not run it in a headless session unless a display/camera are available.

## Build an experiment command

Experiment functions return `(trackers, dataset)` and select tracker lists and datasets inside Python code. Build the command shape with:

```bash
python scripts/build_tracking_command.py experiment --experiment-module myexperiments --experiment-name atom_nfs_uav --threads 0 --debug 0 --explain
```

A typical experiment function uses `trackerlist("atom", "default", range(3))` and `get_dataset("nfs", "uav")`. Verify that the module/function exists in the target checkout and that every selected dataset path is configured before running.

## Visdom and debug behavior

- `debug=0` is the safest default for non-interactive runs.
- With `debug > 0`, PyTracking may start Visdom visualizations or fall back to Matplotlib windows.
- The native CLI uses `argparse type=bool` for `--use_visdom`, so strings such as `False` are truthy. The helper emits an empty-string workaround for `--visdom off`, but the Python API is cleaner when strict Visdom control matters.
- Start a Visdom server separately only when the user wants interactive visualization.

## Python API equivalents

Prefer Python API calls when a larger script already controls configuration:

```python
from pytracking.run_tracker import run_tracker
run_tracker("dimp", "dimp50", dataset_name="otb", sequence="Soccer", debug=0, threads=0)
```

```python
from pytracking.evaluation import Tracker
tracker = Tracker("atom", "default")
# Use tracker.run_sequence(seq, debug=0) after constructing a Sequence object.
```

## Validation before execution

1. Import `pytracking` and `ltr` in the target environment.
2. Confirm `pytracking/evaluation/local.py` exists and has non-empty paths for the selected dataset, network/checkpoints, and result directories.
3. Confirm the tracker/parameter names are source module names, not paper display names.
4. For CUDA-backed trackers, run a tiny `torch.cuda.is_available()` and allocation check.
5. For dataset runs, start with one short sequence before a full benchmark.
6. For video/webcam runs, confirm GUI/display/camera access and output path write permission.
