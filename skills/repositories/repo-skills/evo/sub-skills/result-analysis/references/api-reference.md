# Result API reference

This reference covers the saved-result container, merge strategy, and pandas bridge helpers used by `evo_res` and by programmatic workflows.

## Public container

### `Result`

- Fields:
  - `info` — metadata dictionary.
  - `stats` — scalar statistics dictionary.
  - `np_arrays` — named NumPy arrays, such as `error_array` or `alignment_transformation_sim3`.
  - `trajectories` — optional backup trajectories.
- Methods:
  - `add_info(info_dict)`
  - `add_stats(stats_dict)`
  - `add_np_array(name, array)`
  - `add_trajectory(name, traj)`
  - `pretty_str(title=True, stats=True, info=False)`
- Equality checks compare info, stats, trajectories, and array contents.

## Merge behavior

### `merge_results(results)`

- Requires a non-empty sequence of `Result` objects.
- All results must share the same `stats` and `np_arrays` keys.
- If array lengths match, arrays are averaged element-wise.
- If array lengths differ, raw arrays are appended.
- Info dictionaries come from the first result.

## Archive helpers

### `save_res_file(zip_path, result_obj, confirm_overwrite=False)`

Writes a zip archive containing:
- `info.json`
- `stats.json`
- one `.npy` file per array
- optional `.tum` or `.kitti` trajectory backups

### `load_res_file(zip_path, load_trajectories=False)`

Reads the same archive back into a `Result` object. Use `load_trajectories=True` if you want the backup trajectories restored.

## Pandas helpers

### `result_to_df(result_obj, label=None)`

Converts a single `Result` to a DataFrame-like structure for display or export.

### `load_results_as_dataframe(result_files, use_filenames=False, merge=False)`

Loads multiple archives and stacks them into one DataFrame.

### `save_df_as_table(df, path, format_str='csv', transpose=True, confirm_overwrite=False)`

Exports a DataFrame to csv, Excel, LaTeX, JSON, or another pandas-supported writer.

## Practical notes

- `evo_res` and the pandas bridge are built on the same archive format, so a file that fails to load in one usually fails in the other.
- Result archives are not generic zip files; the `info.json` and `stats.json` members are required.
- Saved trajectories are optional and may be absent by design when the archive was created without backups.
