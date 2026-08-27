# Runtime CLI Reference

## When to read

Read this when you need the exact public launcher flags and their operational
meaning. The verified launcher help exposes only these options.

## `main.py` options

| Flag | Default | Meaning |
| --- | --- | --- |
| `--dataset` | `datasets/tum/rgbd_dataset_freiburg1_desk` | Input selector. May be a supported dataset directory, a video file, an RGB folder, `realsense`, or `webcam`. |
| `--config` | `config/base.yaml` | YAML config to load. Child configs can use `inherit`. |
| `--save-as` | `default` | If not `default`, outputs go under `logs/<save-as>/`. |
| `--no-viz` | false | Disable the OpenGL visualization process and use a fake queue. Essential for headless or evaluation runs. |
| `--calib` | empty string | YAML calibration file with `width`, `height`, and `calibration` list. Forces calibrated mode in addition to the config. |

## Command-building guidance

Use the bundled wrapper to avoid accidental long runs:

```bash
python sub-skills/run-slam/scripts/run_mast3r_slam.py \
  --repo-root <MASt3R-SLAM-checkout> \
  --dataset <dataset-or-video> \
  --config <config-yaml> \
  --save-as <run-name> \
  --no-viz \
  --dry-run
```

Add `--execute` only after the command is reviewed.

## Important runtime facts

- `main.py` sets the multiprocessing start method to `spawn`.
- The runtime device is hard-coded to `cuda:0`.
- `--no-viz` skips the visualization process but does not remove CUDA, MASt3R,
  checkpoints, or backend-extension requirements.
- If `dataset.save_results` is true, old trajectory and PLY files for the same
  sequence are deleted before a new run.
- At run completion, MASt3R-SLAM writes trajectory, reconstruction, and keyframe
  files through `mast3r_slam.evaluate`.
