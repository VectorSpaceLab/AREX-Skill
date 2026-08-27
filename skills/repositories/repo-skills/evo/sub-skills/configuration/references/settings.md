# Settings reference

## File locations
- `~/.evo/settings.json` — user settings file used by `evo_config` and `evo.tools.settings.SETTINGS`
- `~/.evo/evo.log` — global logfile path
- `~/.evo/assets_version` — internal version stamp used to detect settings upgrades

## Load and update behavior
- Importing `evo.tools.settings` creates `~/.evo/` and a fresh settings file if needed.
- If the package version changes, the current settings are soft-merged with the new defaults and the version stamp is updated.
- `SETTINGS` is a dict-like container with dot access for existing keys; unknown attributes raise `SettingsException`.
- Settings files are plain JSON objects written with sorted keys and indentation.

## Merge and reset rules
- `merge_dicts(first, second, soft=False)` is shallow.
- `soft=False` replaces matching top-level keys with values from `second`.
- `soft=True` only fills missing top-level keys from `second`.
- `evo_config set -m other.json` uses that same merge behavior after applying the explicit edits.
- `evo_config reset` writes the default template back to the package settings file.
- `evo_config reset -y key1 key2` only resets those listed keys.
- There is no `-c` override for `reset`.

## Value parsing rules
- Boolean settings toggle when the key is given with no value.
- The strings `true` and `false` are accepted explicitly.
- Numeric tokens are parsed as `int` or `float`.
- List-valued settings accept multiple tokens; `[]` or `none` clears a list.
- `plot_seaborn_palette` is special: a single valid palette name stays a string, while multiple tokens become a literal list of colors.

## Default settings

### Core and logging
- `global_logfile_enabled = false`
- `console_logging_format = "%(message)s"`
- `euler_angle_sequence = "sxyz"`
- `pygments_style = "monokai"`

### Plot and backend
- `plot_backend =` derived by `get_default_plot_backend()`
  - on POSIX with no `DISPLAY` and not macOS: `Agg`
  - if PyQt5 or PyQt6 is importable: `qtagg`
  - otherwise: `TkAgg`
- `plot_seaborn_enabled = true`
- `plot_seaborn_style = "darkgrid"`
- `plot_seaborn_palette = "deep6"`
- `plot_figsize = [10, 10]`
- `plot_fontfamily = "sans-serif"`
- `plot_fontscale = 1.0`
- `plot_linewidth = 1.5`
- `plot_legend_loc = "best"`
- `plot_3d_zoom = 0.9`
- `plot_axis_marker_scale = 0.0`
- `plot_show_axis = true`
- `plot_show_legend = true`
- `plot_split = false`
- `plot_start_end_markers = false`
- `plot_pose_correspondences = false`
- `plot_pose_correspondences_linestyle = "dotted"`
- `plot_invert_xaxis = false`
- `plot_invert_yaxis = false`
- `plot_mode_default = "xyz"`
- `plot_multi_cmap = "none"`
- `plot_reference_alpha = 0.5`
- `plot_reference_color = "#444444"`
- `plot_reference_linestyle = "--"`
- `plot_reference_axis_marker_scale = 0.0`
- `plot_statistics = ["rmse", "median", "mean", "std", "min", "max"]`
- `plot_trajectory_alpha = 0.75`
- `plot_trajectory_cmap = "jet"`
- `plot_trajectory_length_unit = "m"`
- `plot_trajectory_linestyle = "-"`
- `plot_texsystem = "pdflatex"`
- `plot_usetex = false`
- `plot_xyz_realistic = true`

### Geo and map defaults
- `map_tile_provider = "OpenStreetMap.Mapnik"`
- `map_tile_api_token = ""`
- `ros_map_alpha_value = 1.0`
- `ros_map_cmap = "Greys_r"`
- `ros_map_enable_masking = true`
- `ros_map_unknown_cell_value = 205`
- `ros_map_viewport = "keep_unchanged"`

### Rerun, ROS, export, and TF defaults
- `rerun_spawn = true`
- `rerun_viewer_port = 9876`
- `rerun_base_url = "rerun+http://127.0.0.1"`
- `ros2_bag_storage_plugin = "mcap"`
- `ros2_bag_format_version = 9`
- `ros_fallback_frame_id = "world"`
- `save_traj_in_zip = false`
- `table_export_data = "stats"`
- `table_export_format = "csv"`
- `table_export_transpose = true`
- `tf_cache_debug = false`
- `tf_cache_lookup_frequency = 10`
- `tf_cache_max_time = 1e4`

## Safe edit patterns
- Make a writable copy of `~/.evo/settings.json` before experimenting with `set -c`.
- Verify the result with `evo_config show -c <copy> --brief --no_color` or `--diff`.
- Use `generate` to create config JSON from CLI flags instead of hand-editing a file.
- Prefer explicit `true` / `false` values when you do not want boolean toggle semantics.
- `apply_settings()` in `evo.tools.plot` respects the chosen backend, but it does not override the interactive backend inside IPython/Jupyter shells.
