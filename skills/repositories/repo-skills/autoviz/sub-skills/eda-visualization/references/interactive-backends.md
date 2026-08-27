# Interactive backends

AutoViz uses `AutoViz_Holo` for interactive formats:

```python
AV.AutoViz("", dfte=df, chart_format="html", verbose=2, save_plot_dir="interactive-output")
```

## Format choices

- `bokeh`: create interactive Bokeh/HoloViews objects for notebook display.
- `server`, `bokeh_server`, `bokeh-server`: start or display a Panel/Bokeh server route. Use this only when the user asks for a live browser dashboard.
- `html`: save interactive charts as HTML files; this is the safest interactive format for automated or headless agent work.

## Required packages

The interactive route calls `ensure_hvplot_imported()` and needs:

- `hvplot`
- `holoviews`
- `panel`
- `bokeh`
- `IPython` display support

If any of these are missing, the static `png` or `svg` route can still be used for basic EDA.

## Output behavior

- `chart_format='html'` creates a directory when needed and saves files under `AutoViz_Plots/<target>` or `save_plot_dir/<target>`.
- `server` routes may create a live server and are not ideal for noninteractive automated checks.
- Some HoloViews DynamicMap plots can be sensitive to package versions; check `references/install-and-compatibility.md` if users report `ClassSelector` or Bokeh/Panel errors.

## Safe test pattern

Use a tiny DataFrame and the bundled `scripts/autoviz_interactive_smoke.py` script before attempting a large notebook-style workflow.

## When to fall back

Use static `png` or `svg` when:

- The environment has no browser or notebook display.
- The user only needs saved images.
- HoloViews/Bokeh dependency resolution is blocked.
- You need a deterministic smoke test in CI or a headless agent run.
