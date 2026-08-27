# `evo_traj` CLI reference

`evo_traj` is the main trajectory inspection, conversion, and export command.

## Routes and inputs

| Subcommand | Primary input | Notes |
| --- | --- | --- |
| `kitti` | One or more KITTI pose files | Pose-only data, no timestamps. |
| `tum` | One or more TUM trajectory files | Timestamped trajectories. |
| `euroc` | One or more EuRoC CSV files | Timestamped trajectories in EuRoC layout. |
| `bag` | ROS bag file + topics | Needs supported topic names or `--all_topics`. |
| `bag2` / `mcap` | ROS2 bag or MCAP + topics | `mcap` is an alias of `bag2`. |

## Common flags

- `-f`, `--full_check` — print all validation stats.
- `-s`, `--correct_scale` — scale-correct with Umeyama; usually used with `--ref`.
- `--n_to_align N` — use only the first N poses for alignment.
- `--sync` — associate by timestamps; requires `--ref`.
- `--transform_left FILE` — left-multiply a transform.
- `--transform_right FILE` — right-multiply a transform.
- `--propagate_transform` — propagate the right-multiplicative transform through the path.
- `--invert_transform` — invert the loaded transform file.
- `--ref NAME_OR_PATH` — choose the reference trajectory.
- `--t_offset OFFSET` and `--t_max_diff DIFF` — time association controls.
- `--merge` — merge all loaded trajectories into one.
- `--project_to_plane xy|xz|yz` — project to 2D after alignment/transforms.
- `--downsample N` and `--motion_filter DIST ANGLE_DEGREES` — preprocessing controls.
- `--plot`, `--plot_relative_time`, `--plot_mode`, `--save_plot`, `--rerun`, `--save_table` — visualization/export controls.
- `--save_as_tum`, `--save_as_kitti`, `--save_as_bag`, `--save_as_bag2` — export controls.
- `--show_full_names` — keep full input names in summaries.
- `--no_warnings`, `-v`, `--silent`, `--debug`, `-c CONFIG` — usability and config controls.

## Notes that matter in practice

- `--sync` only makes sense when the loaded trajectories have timestamps.
- `--merge` and `--ref` solve different problems: one combines trajectories, the other picks the reference.
- Bag routes fail fast if no supported topics are given and `--all_topics` is not set.
- `bag2` and `mcap` share the same parser and help text, so the same topic rules apply.
- The `--map_tile` and `--ros_map_yaml` options are plot-related extras that depend on the plotting stack and, for map tiles, the `contextily` extra.
