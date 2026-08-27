# Runtime Workflows

## When to read

Read this for concrete, safe command patterns for single MASt3R-SLAM runs.

## Generate config templates

```bash
python sub-skills/run-slam/scripts/write_config_templates.py --output-dir <config-dir>
```

Use those templates as runtime config files instead of relying on a source
checkout's config directory.

## Headless video run

```bash
python sub-skills/run-slam/scripts/run_mast3r_slam.py \
  --repo-root <MASt3R-SLAM-checkout> \
  --dataset <path/to/video.mp4> \
  --config <config-dir>/base.yaml \
  --save-as video-demo \
  --no-viz \
  --dry-run
```

Review the printed command, then replace `--dry-run` with `--execute` when the
GPU, checkpoints, and input are ready.

## RGB folder run with calibration

```bash
python sub-skills/run-slam/scripts/validate_inputs.py --dataset <rgb-folder> --calib <intrinsics.yaml> --strict
python sub-skills/run-slam/scripts/run_mast3r_slam.py \
  --repo-root <MASt3R-SLAM-checkout> \
  --dataset <rgb-folder> \
  --config <config-dir>/calib.yaml \
  --calib <intrinsics.yaml> \
  --save-as rgb-folder-calib \
  --no-viz \
  --dry-run
```

## Benchmark sequence run

For a single benchmark sequence, use the same runtime wrapper with the dataset
sequence path and an evaluation config:

```bash
python sub-skills/run-slam/scripts/run_mast3r_slam.py \
  --repo-root <MASt3R-SLAM-checkout> \
  --dataset <datasets/tum/rgbd_dataset_freiburg1_room> \
  --config <config-dir>/eval_calib.yaml \
  --save-as tum/calib/rgbd_dataset_freiburg1_room \
  --no-viz \
  --dry-run
```

Use the `evaluation` sub-skill when you need whole-suite loops or metrics.

## Live run

```bash
python sub-skills/run-slam/scripts/run_mast3r_slam.py \
  --repo-root <MASt3R-SLAM-checkout> \
  --dataset realsense \
  --config <config-dir>/base.yaml \
  --dry-run
```

RealSense requires camera hardware. Do not use `--no-viz` unless you explicitly
want a headless live run with no visualization feedback.

## Outputs

When `dataset.save_results` is true, outputs are written under `logs/` or
`logs/<save-as>/`:

- `<sequence>.txt`: timestamp, translation, quaternion trajectory rows.
- `<sequence>.ply`: point-cloud reconstruction.
- `keyframes/<sequence>/<timestamp>.png`: keyframe images.

The `--save-as` value is the safest way to keep repeated runs separated.
