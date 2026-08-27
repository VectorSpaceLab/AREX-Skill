# Result-analysis troubleshooting

| Signal | Likely cause | Safe recovery |
| --- | --- | --- |
| `is not a valid result file` | The archive is missing the required `info.json` or `stats.json` members. | Recreate the archive with `save_res_file()` or `evo_ape` / `evo_rpe --save_results`. |
| `Mismatching titles` warning | You are comparing results from different metric titles. | If that is intentional, rerun with `--ignore_title`. Otherwise keep the results separate. |
| Duplicate `est_name` labels | Multiple results use the same embedded estimate name. | Rename one archive with the bundled helper or use `--use_filenames`. |
| `can't merge results with non-matching keys` | The archives do not share the same stats/array keys. | Compare only compatible results or load them separately. |
| `unsupported export data specifier` | `table_export_data` is not one of the supported export kinds. | Set it to `info`, `stats`, or `error_array` before exporting. |
| Plot or table output is missing pieces | The result archive did not include trajectories or the export setting removed them. | Reload with `load_trajectories=True` when backups exist, or save the trajectories in future runs. |
| `Optional dependency rerun-sdk is not installed` | You used the Rerun route without the extra. | Install `rerun-sdk` or drop the `--rerun` flag. |
| `No broken requirements found` is absent after install | The environment may still be inconsistent even though the package imported. | Run `pip check` and reinstall the package into a clean environment if needed. |

## Recovery sequence

1. Confirm the archive came from evo and not from a different tool.
2. Check the embedded `est_name` / title labels before merging or comparing.
3. Decide whether you need the backup trajectories or only the stats and arrays.
4. If you only need a label cleanup, use the safe rename helper instead of editing the zip by hand.
