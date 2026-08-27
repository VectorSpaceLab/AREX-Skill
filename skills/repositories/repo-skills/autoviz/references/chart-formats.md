# Chart formats and output behavior

`AutoViz_Class.AutoViz` dispatches by `chart_format`.

| `chart_format` | Backend route | Typical use | Output behavior |
| --- | --- | --- | --- |
| `svg` | `AutoViz_Main` matplotlib/seaborn | Default notebook or report-friendly static output | Can display inline when `verbose<=1`; can save files when `verbose=2`. |
| `png` | `AutoViz_Main` matplotlib/seaborn | Headless smoke tests or image artifacts | Saves image files when `verbose=2`. |
| `jpg` | `AutoViz_Main` matplotlib/seaborn | Static image output | Same as `png`, with JPEG encoding. |
| `bokeh` | `AutoViz_Holo` | Interactive notebook charts | Requires HoloViews/Bokeh stack; intended for notebook display. |
| `server`, `bokeh_server`, `bokeh-server` | `AutoViz_Holo` | Browser/server dashboards | May start a Panel/Bokeh server; use only when the user wants this behavior. |
| `html` | `AutoViz_Holo` | Saved interactive HTML artifacts | Writes HTML files under `AutoViz_Plots` or `save_plot_dir`. |

## Output-directory rules

- `save_plot_dir=None` defaults to an `AutoViz_Plots` directory under the current working directory for saving modes.
- When a target variable is provided, AutoViz may create a target-named subdirectory under the plot directory.
- `verbose=2` means save plots locally without display.
- `verbose=1` prints more information and displays charts when the runtime supports it.
- `verbose=0` is quieter but still performs the analysis.

## Headless-agent recommendation

For automated checks, prefer:

```python
AV.AutoViz("", dfte=df, verbose=2, chart_format="png", save_plot_dir="autoviz-output")
```

This avoids needing notebook display hooks or a browser session. Use `html` only when testing the HoloViews route and use `server` only when the user explicitly wants a live server.
