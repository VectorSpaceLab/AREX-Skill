# Metrics API reference

This reference covers the public APE/RPE helpers, the CLI routes that reach them, and the semantics of the flags that matter for metrics workflows.

## Public entry points

### CLI commands

| Command | Input route | Sync behavior | Notes |
| --- | --- | --- | --- |
| `evo_ape kitti REF EST` | KITTI pose files | no timestamp association | Use for pose-only trajectories.
| `evo_ape tum REF EST` | TUM trajectory files | timestamp association via `--t_max_diff`, `--t_offset`, `--t_start`, `--t_end` | Best fit for paired timestamped trajectories.
| `evo_ape euroc GT.csv EST.tum` | EuRoC ground truth CSV + TUM estimate | timestamp association | The estimate is read as a TUM trajectory.
| `evo_ape bag BAG REF_TOPIC EST_TOPIC` | ROS bag | timestamp association | Uses `rosbags` and supported ROS message topics.
| `evo_ape bag2 BAG REF_TOPIC EST_TOPIC` / `evo_ape mcap ...` | ROS2 bag or MCAP | timestamp association | `mcap` is an alias of `bag2`.
| `evo_rpe ...` | same routes as `evo_ape` | same sync rules | RPE adds delta and pair-selection controls.

The same routing pattern applies to `evo_rpe`.

### Python helpers

```python
ape(traj_ref, traj_est, pose_relation, align=False, correct_scale=False, n_to_align=-1, align_origin=False, ref_name='reference', est_name='estimate', change_unit=None, project_to_plane=None) -> Result

rpe(traj_ref, traj_est, pose_relation, delta, delta_unit, rel_delta_tol=0.1, all_pairs=False, pairs_from_reference=False, align=False, correct_scale=False, n_to_align=-1, align_origin=False, ref_name='reference', est_name='estimate', support_loop=False, change_unit=None, project_to_plane=None) -> Result
```

Public constructors:

```python
APE(pose_relation=PoseRelation.translation_part)
RPE(pose_relation=PoseRelation.translation_part, delta=1.0, delta_unit=Unit.frames, rel_delta_tol=0.1, all_pairs=False, pairs_from_reference=False)
```

Both helpers return `evo.core.result.Result`. Both operate on the supplied trajectories in place, so call them on copies if you need the originals later.

## Pose relations

| Relation | APE | RPE | Output unit |
| --- | --- | --- | --- |
| `full` / `full_transformation` | yes | yes | unit-less |
| `trans_part` / `translation_part` | yes | yes | meters |
| `rot_part` / `rotation_part` | yes | yes | unit-less |
| `angle_deg` / `rotation_angle_deg` | yes | yes | degrees |
| `angle_rad` / `rotation_angle_rad` | yes | yes | radians |
| `point_distance` | yes | yes | meters |
| `point_distance_error_ratio` | no | yes | percent |

`point_distance_error_ratio` is the only ratio-style relation. It divides the absolute point-distance error by the reference distance and multiplies by 100.

## Delta and pair selection

RPE-specific controls are mapped like this:

| CLI flag | API field | Meaning |
| --- | --- | --- |
| `-d`, `--delta` | `delta` | The pair spacing. Must be positive. |
| `-u`, `--delta_unit` | `delta_unit` | `f` = frames, `d` = degrees, `r` = radians, `m` = meters. |
| `--all_pairs` | `all_pairs` | Search all valid pairs instead of consecutive pairs. |
| `--pairs_from_reference` | `pairs_from_reference` | Choose pair candidates from the reference trajectory instead of the estimate. |
| `-t`, `--delta_tol` | `rel_delta_tol` | Relative tolerance used for all-pairs matching. |

Important details:

- `delta_unit=frames` requires an integer delta.
- `delta_unit=meters`, `degrees`, or `radians` uses a relative tolerance of `delta * rel_delta_tol` when `--all_pairs` is on.
- If no valid pair survives, the helper raises a filter error instead of returning an empty metric.
- For consecutive-pair RPE, the metric is computed on the pairs selected by the delta rules and the first pose is kept only as a plotting anchor.

## Alignment and projection

| Option | Behavior |
| --- | --- |
| `--align` | Umeyama alignment in SE(3). Scale is not corrected. |
| `--correct_scale` | Correct scale only when used without `--align`. With `--align`, this becomes Sim(3) alignment. |
| `--align_origin` | Move the estimate origin to the reference origin. Mutually exclusive with `--align`. |
| `--n_to_align` | Use only the first N poses for Umeyama alignment. `-1` means all available poses. |
| `--project_to_plane xy|xz|yz` | Project both trajectories after any alignment step and before metric evaluation. |

Notes:

- `--align` and `--align_origin` are exclusive. The CLI parser rejects the combination and the Python helpers raise `ValueError` if they are combined.
- `--correct_scale` can still be combined with `--align_origin`; that path first corrects scale and then applies origin alignment.
- `--project_to_plane` mutates the trajectory objects in place. Reuse fresh copies if you need the unprojected data again.

## Preprocessing and synchronization

| Option | Scope | Behavior |
| --- | --- | --- |
| `--downsample N` | both trajectories | Keep at most N poses with even spacing. This runs before synchronization. |
| `--motion_filter DIST ANGLE_DEGREES` | both trajectories | Drop poses whose motion to the previous kept pose is below either threshold. This also runs before synchronization. |
| `--t_start`, `--t_end` | timestamped routes only | Crop the time range before association. |
| `--t_offset` | timestamped routes only | Shift the second trajectory timestamps before matching. |
| `--t_max_diff` | timestamped routes only | Maximum timestamp gap accepted during matching. |

`--motion_filter` requires timestamped trajectories in metrics workflows; the CLI protects against applying it to path-only data because it could break association.

## Output, plots, rerun, and result zips

| Option | Behavior |
| --- | --- |
| `--save_plot PATH` | Export the combined plot collection to `PATH`. |
| `--plot` | Show the plot window. |
| `--plot_x_dimension` | Use `index`, `seconds`, or `distances` on the raw-value plot x-axis. Seconds fall back to index when no timestamps exist. |
| `--rerun` | Send the trajectories, error array, and statistics to Rerun. Requires the optional `rerun-sdk` dependency. |
| `--rerun_rec_id` | Reuse or append to a specific Rerun recording id. |
| `--save_results PATH.zip` | Save the `Result` object as a zip file. |

Result zip semantics:

- The archive always stores `info.json` and `stats.json`.
- Each `Result.np_arrays` entry is written as a separate `.npy` file, such as `error_array.npy` or `alignment_transformation_sim3.npy`.
- Backup trajectories are written only when they are still present in the `Result` object at save time.
- The CLI strips trajectories before saving unless the package setting for keeping trajectories in zips is enabled.
- `load_res_file(PATH, load_trajectories=True)` rehydrates saved trajectory backups when they are present.

## Conversion rules for `--change_unit`

`--change_unit` uses the same `Unit` values as the API and only changes compatible unit families.

- Length units: `mm`, `cm`, `m`, `km`
- Angle units: `deg`, `rad`
- Not convertible: `unit-less`, `frames`, `seconds`, `percent`

If you ask for an incompatible conversion, the metric raises a conversion error instead of silently changing the values.

## Practical reminders

- `ape` and `rpe` mutate the supplied trajectories during alignment and projection, so make copies if you need to preserve the originals.
- `rpe(..., support_loop=True)` deep-copies the trajectories before it trims them down to the delta pairs, which is useful when you call the helper repeatedly in notebooks or loops.
- `APE` and `RPE` constructors are the right place to check metric defaults; `evo.main_ape.ape` and `evo.main_rpe.rpe` are the wrappers used by the CLI.
