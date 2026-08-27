# Python API troubleshooting

| Signal | Likely cause | Safe recovery |
| --- | --- | --- |
| Plot windows do not appear | The current Matplotlib backend is headless or incompatible with the session. | Set a backend before importing plotting code, or use the package defaults for the current environment. |
| `plot.apply_settings()` seems ignored inside a notebook | IPython/Jupyter intentionally preserves the session backend. | Configure the backend before the first plotting import, or use the shell's own `%matplotlib` controls. |
| `ImportError` for `PyQt6` or `PyQt5` | The optional GUI backend is not installed. | Install `evo[gui]` or use a noninteractive backend such as `Agg`. |
| `ImportError` for `contextily` | The geo/map-tile extra is missing. | Install `evo[geo]` or skip map tiles. |
| `Optional dependency rerun-sdk is not installed` | The Rerun integration was requested without the extra. | Install `evo[rerun]` or drop the Rerun path. |
| The example script blocks on a window | The original example was written as an interactive demo. | Use the bundled smoke helper or export a figure to a file instead of calling `show()`. |
| Pandas conversion loses timestamps or type information | The wrong trajectory type or index was used in the round-trip. | Use `PoseTrajectory3D` for timestamped data, `PosePath3D` for path-only data, and keep the DataFrame index intact. |
| The plotting output looks empty or partially clipped | The figure size or backend settings are unsuitable for the data. | Adjust `plot_figsize`, `plot_3d_zoom`, or export to a file and inspect the axes. |

## Recovery sequence

1. Start from a synthetic smoke run with `scripts/programmatic_api_smoke.py`.
2. Confirm the backend and optional extras needed by the workflow.
3. Deep-copy trajectories before reusing them across multiple helper calls.
4. If the workflow needs the original source example to make sense, distill it into the bundled reference or smoke helper instead of depending on the original checkout.
