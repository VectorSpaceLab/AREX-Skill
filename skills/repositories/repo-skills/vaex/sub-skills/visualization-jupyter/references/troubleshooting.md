# Visualization and widget troubleshooting

Use this guide when a Vaex plotting or widget workflow fails, renders nothing, or emits a surprising warning. If the issue is really a computation problem, route to [../../expressions-analytics/SKILL.md](../../expressions-analytics/SKILL.md). If it is a DataFrame construction problem, use [../../dataframe-core/SKILL.md](../../dataframe-core/SKILL.md).

## Quick triage

Run a tiny smoke check before escalating a plot issue:

```bash
python scripts/plot_smoke.py --help
python scripts/plot_smoke.py
```

For notebook environments, also confirm the frontend packages you expect are available.

## Failure matrix

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError` for `vaex.viz` or `matplotlib` | The visualization package or Matplotlib is not installed in the active environment | Install the public plotting dependencies, then re-run a tiny `df.viz` smoke check. `df.viz` and `expression.viz` require the plotting stack to be present. |
| Plotting fails with a headless or display-related error | A GUI backend was selected in a terminal or server session | Force `matplotlib.use("Agg")` before importing `pyplot`, keep `show=False`, and save with `hardcopy=` or `plt.savefig(...)`. On newer Matplotlib builds where `matplotlib.cm.get_cmap` was removed, apply the compatibility shim used in `scripts/plot_smoke.py` before retrying Vaex heatmaps or server plot endpoints. |
| `ValueError` about `what` | The statistic string is not in Vaex’s small expression grammar | Use `count(*)`, `mean(x)`, `sum(x)`, `std(x)`, or `correlation(a, b)`. Validate the syntax on a small sample before trying a bigger plot. |
| `ValueError` about `facet` or `z` layout strings | The facet spec is malformed | Use the `name:low,high,count` form, such as `facet="bin:-1,1,8"` or `z="FeH:-3,1,5"`. Keep commas and parentheses out of the expression part unless they are part of the actual Vaex expression. |
| Scatter plot raises the row-limit error | `df.viz.scatter` only supports small DataFrames or bounded selections by default | Narrow the selection, lower the row count, or switch to an aggregated heatmap/histogram. You can also raise `length_limit` if you are certain the data is still small enough. |
| `plot1d`, `scatter`, or `plot` emits a deprecation warning | You are using the compatibility shim instead of the current API | Prefer `df.viz.histogram`, `df.viz.scatter`, and `df.viz.heatmap` in new guidance. |
| Widget object exists but nothing renders | The notebook/Voila frontend or extension is missing | Check `ipywidgets`, `bqplot`, `ipyvuetify`, `ipympl`, `ipyvolume`, and `ipyleaflet`. In a terminal session, do not expect widget rendering at all; use static `df.viz` output instead. |
| `progress='widget'` does not show a notebook progress bar | The notebook frontend is missing, disabled, or not a widget-capable environment | Use `progress=True` or `vaex.progress.tree('rich', ...)` in the terminal, or install/enable the widget frontend in the notebook. |
| `df.widget.data_array(...)` creates a view but `model.grid` is still `None` | The grid calculation is asynchronous and has not finished yet | Wait for completion with `vaex.jupyter.gather()` or trigger the computation path that the widget expects. |
| Progress counter or selection counter does not update when expected | The computation never ran, or the selection state is not the one the widget tracks | Trigger a computation, confirm the selection name, and use the counter helper that matches the current frontend style. |

## Safe recovery playbooks

### Static plotting from a terminal

1. Force the noninteractive backend before importing `pyplot`.
2. Create tiny in-memory data or a bounded selection.
3. Use `hardcopy=` for histograms and heatmaps.
4. Save scatter plots with `plt.gcf().savefig(...)`.
5. Assert the file exists and is non-empty.

### Invalid plot grammar

1. Reduce the example to a tiny DataFrame.
2. Try a known-good expression like `count(*)` or `mean(x)`.
3. Rebuild the `facet` or `z` string with the `name:low,high,count` pattern.
4. If the statistic is custom, route the computation to [../../expressions-analytics/SKILL.md](../../expressions-analytics/SKILL.md) and render the result here.

### Large scatter or dense plot

1. Check whether the user really wants raw points or an aggregated summary.
2. Prefer heatmap/histogram for dense data.
3. Restrict scatter with `selection`, `limits`, or a smaller DataFrame.
4. Keep `length_limit` as a guardrail, not something to bypass casually.

### Widget frontend not rendering

1. Confirm the Python object is actually a widget, not just a plain return value.
2. Check that the notebook/Voila frontend stack is installed.
3. Make sure the widget is displayed explicitly.
4. If you are in a terminal, switch to a static `df.viz` plot or a progress log.

## Frontend package checklist

If a notebook widget does not render, review the optional frontend layers one by one:

- `ipywidgets`
- `bqplot`
- `ipyvuetify`
- `ipyvolume`
- `ipyleaflet`
- `ipympl`

Not every environment has every frontend package. The safe fallback is usually a static Matplotlib plot or a terminal progress display.