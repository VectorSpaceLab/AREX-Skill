# `run_slam.py` CLI reference

The parser accepts one positional `config_path`. All other options are
optional. Values are applied after YAML inheritance, by
`update_config_with_args` in `run_slam.py`.

## Paths and experiment labels

| Option | Type | Effective field/behavior | Notes |
|---|---|---|---|
| `config_path` | string | input to `load_config` | Required. Inheritance paths are resolved as written by the process. |
| `--input_path PATH` | string | `data.input_path` | Applied when non-empty. |
| `--output_path PATH` | string | `data.output_path` | Applied when non-empty. Use an explicit path; do not rely on the source's timestamp fallback. |
| `--project_name NAME` | string | `project_name` | Only used when W&B is enabled. |
| `--group_name NAME` | string | W&B group argument | Not stored in the config and not a general experiment label. |

## Tracking options

| Option | Type | Effective field | Notes |
|---|---|---|---|
| `--track_w_color_loss VALUE` | float | **none** | Parsed but never copied by `update_config_with_args`; edit YAML instead. |
| `--track_alpha_thre VALUE` | float | `tracking.alpha_thre` | Applied when not `None`. |
| `--track_iters N` | int | `tracking.iterations` | Applied when not `None`. |
| `--track_filter_alpha` | flag | `tracking.filter_alpha = True` | One-way enable. |
| `--track_wo_filter_alpha` | flag | `tracking.filter_alpha = False` | If both filter flags are supplied, this later assignment wins. |
| `--track_filter_outlier` | flag | `tracking.filter_outlier_depth = True` | One-way enable. |
| `--track_wo_filter_outlier` | flag | `tracking.filter_outlier_depth = False` | If both outlier flags are supplied, this later assignment wins. |
| `--track_cam_trans_lr VALUE` | float | `tracking.cam_trans_lr` | Applied only when the value is truthy; zero is ignored. |
| `--help_camera_initialization` | flag | `tracking.help_camera_initialization = True` | One-way enable. It permits odometer fallback for a high-loss initialization. |
| `--soft_alpha` | flag | `tracking.soft_alpha = True` | One-way enable. |
| `--gt_camera` | flag | **none** | Parsed but never copied; it does not select ground-truth tracking. Set `tracking.odometry_type: gt` in YAML. |

The parser does not expose `odometry_type`, `odometer_method`, camera rotation
learning rate, `init_err_ratio`, or `mask_invalid_depth`. Change those in the
resolved YAML. The source tracker uses the spelling `odometry_type`; do not
invent a CLI alias.

## Mapping options

| Option | Type | Effective field | Notes |
|---|---|---|---|
| `--alpha_seeding_thre VALUE` | float | `mapping.alpha_thre` | Applied when not `None`; this is the mapper seeding threshold, not tracking alpha. |
| `--map_every N` | int | `mapping.map_every` | Applied only when truthy; zero is ignored and is not a valid useful cadence. |
| `--map_iters N` | int | `mapping.iterations` | Applied only when truthy; zero is ignored. |
| `--new_submap_every N` | int | `mapping.new_submap_every` | Applied only when truthy; zero is ignored. Used when motion heuristic is false. |
| `--submap_using_motion_heuristic` | flag | `mapping.submap_using_motion_heuristic = True` | One-way enable; there is no CLI flag to force false. |
| `--new_submap_points_num N` | int | `mapping.new_submap_points_num` | Applied only when truthy; negative values are truthy and mean all points in the source seeding branch. |

There is no CLI override for `new_submap_iterations`,
`new_submap_gradient_points_num`, `new_frame_sample_size`, `new_points_radius`,
`current_view_opt_iterations`, or `pruning_thre`.

## Seed and W&B disable

| Option/environment | Effective behavior | Notes |
|---|---|---|
| `--seed N` | `seed = N` only if `N` is truthy | `--seed 0` is ignored; use YAML for seed zero. |
| `DISABLE_WANDB=true` | forces `use_wandb = False` | Comparison is exact and lowercase. Other values do not disable W&B. |
| `use_wandb: true` | `wandb.init`, code logging, per-iteration logs, and post-eval metric logs | Requires a writable W&B directory and whatever online/offline setup the site chooses. No credentials are needed when disabled. |

## Safe construction examples

Basic run:

```bash
DISABLE_WANDB=true python run_slam.py configs/Replica/room0.yaml \
  --input_path <scene-input> --output_path <output/replica-room0>
```

Positive seed and diagnostic tracking override:

```bash
DISABLE_WANDB=true python run_slam.py configs/<dataset>/<scene>.yaml \
  --input_path <scene-input> --output_path <output/<scene>-seed1> \
  --seed 1 --track_iters 20 --map_every 10
```

These are execution commands and should only be run after CUDA/extension and
input checks. The bundled `check_cli.py` is the safe alternative for checking
config/override intent without starting SLAM.
