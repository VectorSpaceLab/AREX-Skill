# Jupyter widgets

Use this guide for Vaex notebook widgets, dashboard composition, and progress feedback. It complements `df.viz`/`expression.viz` by covering interactive views rather than static plots.

## Widget families

Vaex exposes a small set of high-level widget accessors that are usually enough for notebook and Voila workflows:

- `df.widget.data_array(...)`: build a widget-backed xarray-style data view from one or more axes.
- `df.widget.histogram(...)` and `df.widget.heatmap(...)`: bqplot-based interactive visualizations.
- `df.widget.expression(...)` and `df.widget.column(...)`: editable controls for expressions or columns.
- `df.widget.selection_expression(...)`: editable named selections.
- `df.widget.progress_circular(...)`, `df.widget.counter_processed(...)`, and `df.widget.counter_selection(...)`: progress/status helpers.

The `data_array` accessor is the most flexible entry point. It creates axis models, links them to a view, and accepts an optional `display_function` callback. The callback receives an xarray `DataArray` object and can render with Matplotlib, Plotly, ipyvolume, or another widget system.

```python
import vaex
import vaex.jupyter.model as vjm
import matplotlib.pyplot as plt


df = vaex.from_arrays(x=[-2, -1, 0, 1, 2], y=[4, 1, 0, 1, 4])
x_axis = vjm.Axis(df=df, expression=df.x)
y_axis = vjm.Axis(df=df, expression=df.y)
view = df.widget.data_array(axes=[x_axis, y_axis], selection=[None, "default"])
```

## High-level interactive patterns

- Use `selection=[None, "default"]` when you want the widget to show both the full data and a named selection.
- Use `shared=True` if several widgets should reuse the same grid calculator.
- Use `vaex.jupyter.gather()` when the grid or axis limits are computed asynchronously and you need to wait for completion before reading `model.grid`.
- Use `traitlets.link` or `ipywidgets.link` to keep an `Axis` and an editor widget synchronized.
- Use `ContainerCard`, `LinkList`, and `ToolsToolbar` when you want a compact dashboard-style layout.

Example of a linked expression editor:

```python
from traitlets import link

expr_widget = df.widget.expression(x_axis, label="X axis")
link((expr_widget, "value"), (x_axis, "expression"))
```

## Progress feedback

Progress in notebook contexts should match the frontend that is actually available:

- `progress='widget'` is for notebook/widget environments.
- `progress=True` gives a plain progress indicator.
- `vaex.progress.tree('rich', ...)` is better for terminal workflows with nested task detail.

The widget helpers are also useful for dashboard status:

- `progress_circular(auto_hide=True)` shows a compact indicator while computations run.
- `counter_processed()` keeps a running total of processed rows.
- `counter_selection(...)` tracks a named selection and can run lazily so it does not force extra passes.

## Frontend dependency map

Treat these as optional front-end dependencies that may be present or absent:

- `ipywidgets`: base notebook widget runtime.
- `bqplot`: built-in histogram and heatmap widgets.
- `ipyvuetify`: dashboard containers and toolbar components.
- `ipyvolume`: 3D/volume-style custom widget examples.
- `ipyleaflet`: map-style widget examples.
- `ipympl`: Matplotlib widget backend.
- `xarray`: the `data_array` display surface.

If a widget object exists in Python but nothing renders, the likely issue is the notebook frontend rather than the Vaex model.

## Practical dashboard rule

Keep the widget layer responsible for interaction, and keep the data model responsible for numbers. If the dashboard needs a new statistic, build it in the analytics layer first; then expose it through the widget layer for display or control.