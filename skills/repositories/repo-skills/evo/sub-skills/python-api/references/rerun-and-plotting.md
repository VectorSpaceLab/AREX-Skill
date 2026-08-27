# Rerun and plotting notes

This page collects the optional visualization details that often matter when a Python workflow or notebook is not behaving as expected.

## Plot backend behavior

- `plot_backend` defaults to `Agg` on POSIX systems without a display, except on macOS where the default follows the platform path.
- If PyQt5 or PyQt6 is installed, evo can use a Qt-based backend such as `qtagg`.
- If neither Qt backend is available, evo may fall back to `TkAgg`.
- `plot.apply_settings()` deliberately avoids overriding the backend inside IPython/Jupyter shells.

## Practical backend tips

- For headless scripts, set the backend before importing evo plotting helpers.
- For interactive desktop plotting, set `plot_backend` with `evo_config` and rerun the shell.
- If plots render but windows never appear, the environment may be headless or the wrong backend may be active.

## Rerun integration

- Rerun support is optional and depends on `rerun-sdk >= 0.34.0`.
- `evo.tools.rerun_bridge.connect_or_spawn()` can connect to or spawn the viewer.
- `rerun_spawn` controls whether evo should try to spawn the viewer automatically.
- `evo_config set rerun_spawn false` is useful when you want to manage the viewer yourself.

## Geo / map tiles

- `contextily` is optional and only needed for georeferenced map-tile plots.
- Some providers need an API token; evo stores it in the `map_tile_api_token` setting.
- `contextily_helper.get_provider()` rejects provider bunches and expects a real tile provider name such as `OpenStreetMap.Mapnik`.

## Example scripts and notebooks

- `examples/custom_app.py` demonstrates a custom APE plus plotting workflow.
- `examples/alignment_demo.py` shows alignment and plotting behavior.
- `examples/rerun_example/rerun_example.py` demonstrates the optional Rerun route and is best treated as a reference recipe, not a hard runtime dependency.
