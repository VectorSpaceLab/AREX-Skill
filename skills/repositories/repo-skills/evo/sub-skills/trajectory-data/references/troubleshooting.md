# Trajectory troubleshooting

| Signal | Likely cause | Safe recovery |
| --- | --- | --- |
| `TUM trajectory files must have 8 entries per row` | Wrong number of columns or a trailing delimiter. | Fix the file layout or regenerate it with `write_tum_trajectory_file()`. |
| `KITTI pose files must have 12 entries per row` | Wrong number of values per pose row. | Re-export the KITTI file or use the bundled converter from a valid pose file plus timestamps. |
| `EuRoC format ground truth must have at least 8 entries per row` | Invalid EuRoC CSV layout. | Check the source CSV and make sure the timestamp and pose columns are present. |
| `timestamp file must have one column ... and same number of rows` | The KITTI pose file and timestamp file do not match. | Regenerate the timestamp companion file or use the bundled `kitti_timestamps_to_tum.py` helper. |
| `Path doesn't exist` or `File doesn't exist` | The bag, transform, or trajectory file path is wrong. | Correct the path and retry. |
| `No topics used - specify topics or set --all_topics` | A bag route was used without topic selection. | Pass one or more topic names or `--all_topics` / `--all_channels`. |
| `unsupported message type` | The bag topic exists but is not one of evo's supported pose-bearing message types. | Switch to a supported topic or to a TF identifier. |
| `trajectories without timestamps can't be motion filtered` | You tried to motion-filter path-only data. | Use a timestamped trajectory or skip motion filtering for that path-only input. |
| `path was already projected once` | The same object was projected twice. | Re-read or deepcopy the data before applying a second projection. |
| `Cannot determine type of ...` or `doesn't contain a valid Sim(3) or SE(3) matrix` | The transform file is not a supported JSON, `.npy`, or 4x4 text matrix. | Rewrite the transform in one of the supported formats and retry. |
| Duplicate timestamps keep showing up in sync workflows | The source trajectory has repeated timestamps or unsorted input. | Run `scripts/check_duplicate_timestamps.py` and fix the data before syncing. |

## Recovery sequence

1. Validate the file layout with the closest bundled helper or with `--full_check`.
2. Check timestamps and duplicates before blaming alignment or synchronization.
3. Re-read the data into a fresh object before projecting or mutating it again.
4. If the issue is with live ROS recording, remember that `contrib/record_tf_as_posestamped_bag.py` is reference-only and not part of the runtime skill.
