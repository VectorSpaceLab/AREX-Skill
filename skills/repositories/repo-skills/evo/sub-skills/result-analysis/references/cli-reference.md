# `evo_res` CLI reference

`evo_res` loads one or more saved result archives, compares them, optionally merges them, and can export tables or plots.

## Flags that matter most

- `result_files ...` — one or more evo result `.zip` files.
- `--merge` — merge all results into one synthetic result before display.
- `--use_rel_time` — prefer relative timestamps when building comparison tables.
- `--use_filenames` — label columns with filenames instead of embedded `est_name` values.
- `--ignore_title` — skip title matching when aggregating mixed metrics.
- `-p`, `--plot` — show the plot window.
- `--plot_markers` — use circle markers.
- `--save_plot PATH` — export the plot(s).
- `--save_table PATH` — export the loaded table data.
- `--rerun` and `--rerun_rec_id` — optional visualization integration.
- `--logfile PATH` — route logging to a local file.
- `--no_warnings` — suppress overwrite / confirmation prompts where supported.
- `-v`, `--verbose`, `--silent`, `--debug`, `-c CONFIG` — usual usability and config controls.

## Behavior that matters in practice

- The command expects archives created by `save_res_file()` or by `evo_ape` / `evo_rpe` with `--save_results`.
- If the result titles differ and `--ignore_title` is not set, `evo_res` warns before aggregating.
- Duplicate `est_name` labels can make the output ambiguous; `--use_filenames` is the easiest fix.
- The command can show plots, save plots, save tables, and send data to Rerun from the same loaded archive set.
- `--save_table` honors the table export settings in `evo_config` / `evo.tools.settings`.
