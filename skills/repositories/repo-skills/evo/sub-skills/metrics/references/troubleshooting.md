# Metrics troubleshooting

Use these signals to identify metric-specific failures quickly.

| Signal | Likely cause | What to do |
| --- | --- | --- |
| `align and align_origin can't be used simultaneously` | Both alignment modes were requested. | Keep only one. `--align` is Umeyama alignment; `--align_origin` only matches the first pose to the reference origin. |
| `found no matching timestamps between ...` | The timestamp window is too strict, or the offset is wrong. | Increase `--t_max_diff`, fix the sign or size of `--t_offset`, or crop the inputs with `--t_start` / `--t_end`. |
| `trajectories without timestamps can't be motion filtered in metrics` | `--motion_filter` was applied to path-only data. | Use timestamped trajectories or skip motion filtering. |
| `delta must be integer for delta unit ...frames` | Frame-based RPE spacing was given a non-integer delta. | Pass an integer delta or switch to a meter/angle unit. |
| `delta = ... produced an empty index list` | The delta or tolerance is too strict for the available data. | Lower `delta`, loosen `--delta_tol`, or switch on `--all_pairs`. |
| `Ignoring N zero divisions in ratio calculations.` | `point_distance_error_ratio` hit zero reference distances. | Remove zero-length reference segments or choose a different metric. If every qualifying pair has zero distance, the ratio metric is unsafe for that dataset. |
| `cannot convert ...` or `does not support conversions` | `--change_unit` asked for an incompatible conversion. | Convert only within length units or within angle units. Do not expect conversions for unit-less, frames, seconds, or percent. |
| `Optional dependency rerun-sdk is not installed` | `--rerun` was used without the optional package. | Install `rerun-sdk` or drop `--rerun`. |
| `File doesn't exist` / `no messages for topic` / `unsupported message type` | The bag path, topic name, or topic type is wrong. | Fix the path or topic, or use a supported ROS pose topic / TF identifier. |
| `path was already projected once` | The same trajectory object was projected twice. | Work on fresh copies when reusing trajectories programmatically. |
| Saved zip loads without trajectories | Trajectory backups were not written. | This is expected when the result was saved without backup trajectories. Re-load only the stats/arrays, or save the trajectories if you need them. |

Additional checks:

- If the error curve looks correct but the title still says `not aligned`, confirm that `--align` or `--align_origin` was actually passed to the CLI or helper.
- If RPE looks empty or much shorter than expected, remember that the first pose is retained only for plotting and does not have an RPE value.
- If a point topic produces rotation-related surprises, use a pose-bearing topic or a distance-only pose relation.
