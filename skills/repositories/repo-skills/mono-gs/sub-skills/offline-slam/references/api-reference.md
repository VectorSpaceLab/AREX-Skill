# API Reference

This page distills the offline-SLAM facts needed to plan a MonoGS run without
reading the source checkout.

## Command-line entry point

`slam.py` accepts only:

- `--config <path>`
- `--eval`

`--eval` is a runtime override, not a config flag. It forces headless
evaluation-friendly behavior inside `slam.py`.

## Core runtime signatures

| Object | Signature | Role in offline SLAM |
| --- | --- | --- |
| `SLAM` | `SLAM(config, save_dir=None)` | Main orchestration object. It builds the model, dataset, frontend, backend, queues, optional GUI, and then executes the run. |
| `FrontEnd` | `FrontEnd(config)` | Main-process tracking and keyframe logic. Its `run()` method consumes dataset frames, updates poses, and sends mapping work to the backend. |
| `BackEnd` | `BackEnd(config)` | Spawned mapping process. It optimizes Gaussians, manages densification/pruning, and handles color refinement. |
| `load_config` | `load_config(path, default_path=None)` | Recursively resolves `inherit_from` and merges the YAML config tree. |
| `load_dataset` | `load_dataset(args, path, config)` | Returns the dataset wrapper selected by `Dataset.type`. |
| `GaussianModel` | `GaussianModel(sh_degree: int, config=None)` | Owns the splats, optimizer state, point-cloud creation, pruning, densification, and PLY export. |
| `render` | `render(viewpoint_camera, pc, pipe, bg_color, scaling_modifier=1.0, override_color=None, mask=None)` | Rasterizes Gaussians and returns image, visibility, radii, depth, opacity, and touch counts. |
| `Camera` | `Camera.init_from_dataset(dataset, idx, projection_matrix)` | Wraps one frame, pose deltas, exposures, and projection state. |

## Runtime behavior facts

- `slam.py` calls `mp.set_start_method("spawn")` before any worker creation.
- The frontend object is executed in the main process; the backend is started as
  a separate `torch.multiprocessing.Process`.
- A GUI process is created only when `Results.use_gui` is true.
- When `use_gui` is false, the GUI queues are replaced with `FakeQueue`.
- If `Dataset.type == "realsense"`, the run is treated as live mode and GUI is
  forced on. That path belongs to `live-demo`, not this sub-skill.
- `Training.monocular` is assigned at runtime from the dataset sensor type.
- `GaussianModel.sh_degree` is set to `3` when spherical harmonics are enabled,
  otherwise `0`.
- `save_results` enables creation of a timestamped result directory and a copy of
  the merged config as `config.yml`.

## Dataset wrappers selected by `Dataset.type`

| Dataset type | Wrapper | Sensor mode | Practical offline use |
| --- | --- | --- | --- |
| `tum` | `TUMDataset` | `monocular` or `depth` | Monocular TUM and RGB-D TUM configs. |
| `replica` | `ReplicaDataset` | `depth` | RGB-D Replica configs. |
| `euroc` | `EurocDataset` | `stereo` | Stereo EuRoC configs. |
| `realsense` | `RealsenseDataset` | live depth or monocular | Out of scope for offline SLAM. |

## Config keys that matter here

| Key | Used by | Why it matters |
| --- | --- | --- |
| `Dataset.type` | `load_dataset`, `SLAM` | Chooses the offline family. |
| `Dataset.sensor_type` | dataset and loss code | Chooses monocular, depth, or stereo behavior. |
| `Dataset.dataset_path` | dataset wrappers, save-dir naming | Points to the on-disk dataset layout and influences the result folder label. |
| `Dataset.single_thread` | backend | Switches the backend into the serialized mapping path when present. |
| `Training.single_thread` | frontend | Frontend throttling / request pacing. |
| `Results.use_gui` | `SLAM` | Enables or suppresses the GUI process. |
| `Results.save_results` | `SLAM`, `eval_utils` | Enables result-tree creation and periodic exports. |
| `Results.save_trj` | `FrontEnd` | Controls periodic trajectory exports. |
| `Results.eval_rendering` | `SLAM` | Enables the extra rendering pass at the end of a run. |
| `Training.kf_interval`, `window_size`, `pose_window` | frontend/backend | Control keyframe cadence and the mapping window. |
| `Training.alpha` | RGB-D loss code | Balances RGB and depth losses for depth-bearing sensors. |

## Gaussian-model methods used by offline SLAM

- `init_lr(spatial_lr_scale)` — sets the scale used for learning-rate schedules.
- `training_setup(training_args)` — installs the optimizer and learning-rate
  schedule.
- `extend_from_pcd_seq(cam_info, kf_id=-1, init=False, scale=2.0, depthmap=None)`
  — seeds a new keyframe point cloud.
- `densify_and_prune(max_grad, min_opacity, extent, max_screen_size)` — expands
  and prunes points during mapping.
- `reset_opacity()` and `reset_opacity_nonvisible(...)` — opacity maintenance.
- `save_ply(path)` — writes the final or intermediate Gaussian point cloud.

## Renderer return values

`render(...)` returns a dictionary with these keys:

- `render`
- `viewspace_points`
- `visibility_filter`
- `radii`
- `depth`
- `opacity`
- `n_touched`

Offline SLAM uses those values for tracking, mapping, keyframe selection, and
output/export steps.
