# Offline SLAM Workflows

## Command grammar

The runtime entry point is:

```bash
python slam.py --config <config-yaml> [--eval]
```

`slam.py` does **not** accept a runtime `--headless` flag. Headless
operation is created by the config plus `--eval`, or by editing the config copy
so `Results.use_gui: false`.

## Canonical offline configs

| Goal | Config family | Typical command | Notes |
| --- | --- | --- | --- |
| Monocular TUM | `configs/mono/tum/*.yaml` | `python slam.py --config configs/mono/tum/fr3_office.yaml` | Uses `Dataset.sensor_type: monocular`. The loader synthesizes depth for initialization and tracking losses. |
| RGB-D TUM | `configs/rgbd/tum/*.yaml` | `python slam.py --config configs/rgbd/tum/fr3_office.yaml` | Uses depth directly. This is the straight RGB-D offline path. |
| RGB-D Replica | `configs/rgbd/replica/*.yaml` and `*_sp.yaml` | `python slam.py --config configs/rgbd/replica/office0.yaml` | The shipped `_sp` configs are the closest serialized variant. They still use spawned processes, but they also set the backend-side `single_thread` flag. |
| Stereo EuRoC | `configs/stereo/euroc/*.yaml` | `python slam.py --config configs/stereo/euroc/mh02.yaml` | Uses stereo disparity from the left/right pair and the EuRoC calibration block. |

## GUI and headless choices

- Offline configs usually start with `Results.use_gui: true`.
- When `Results.use_gui` is true, `slam.py` starts a GUI process and uses real
  multiprocessing queues.
- When `Results.use_gui` is false, the GUI queues become fake no-op queues and
  the run stays headless.
- `--eval` always forces `save_results: true`, `use_gui: false`,
  `eval_rendering: true`, and `use_wandb: true` inside `slam.py`.
- For a non-eval headless run, create a config copy with `Results.use_gui: false`
  instead of inventing a runtime flag.

## Multiprocessing and `single_thread`

- `slam.py` sets `torch.multiprocessing` start method to `spawn`.
- The backend is launched in a spawned process.
- The frontend logic runs in the main process.
- The GUI, when enabled, is a separate spawned process.
- `Training.single_thread` is read by the frontend.
- `Dataset.single_thread` is read by the backend when present.
- Replica base configs set `Training.single_thread: true`; the `_sp` variants
  also set `Dataset.single_thread: true`.
- If those flags disagree, you are on a mixed path: the frontend may throttle
  while the backend still uses the multi-process mapping loop.

## Sensor-specific notes

- Monocular TUM uses `Dataset.sensor_type: monocular` and `Training.monocular`
  is set at runtime from that sensor type.
- RGB-D TUM and Replica use `Dataset.sensor_type: depth`.
- Stereo EuRoC uses `Dataset.sensor_type: stereo` and a stereo disparity build
  path inside `utils/dataset.py`.
- `Training.monocular` should be treated as a runtime-derived field, not as a
  manual edit target.

## Runtime outputs

When `Results.save_results` is true, `slam.py` creates a timestamped save tree
under `Results.save_dir` and writes the effective config back to `config.yml`.
The exact directory label is derived from the configured dataset path.

Expected outputs include:

- `config.yml` — effective merged config used for the run.
- `plot/trj_<label>.json` and `plot/stats_<label>.json` — trajectory snapshots
  and ATE stats when trajectory saving or eval is enabled.
- `plot/evo_2dplot_<label>.png` — trajectory plot generated during evaluation.
- `point_cloud/iteration_<n>/point_cloud.ply` or `point_cloud/final/point_cloud.ply`
  — Gaussian point cloud export.
- `psnr/<iteration>/final_result.json` — rendering summary when evaluation
  rendering is enabled.
- W&B tables/logs when `use_wandb` is enabled.

Periodic trajectory exports only happen when both `save_results` and `save_trj`
are true.

## Safe preflight checklist

1. Resolve the repo root and config path.
2. Confirm the config inherits from an offline family, not `configs/live/*`.
3. Check that the repo root contains `slam.py`, `utils/`, `gaussian_splatting/`,
   `gui/`, and `scripts/`.
4. If the run should be headless, either use `--eval` or prepare a config copy
   with `Results.use_gui: false`.
5. If you want a serialized Replica-style run, prefer the `_sp` config variant.
6. Use `scripts/plan_slam_run.py` to print the exact command before launching
   any long SLAM job.
