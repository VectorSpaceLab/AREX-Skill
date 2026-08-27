# Visualization workflows

Use this guide for rendering Vaex data with `df.viz` or `expression.viz`, for saving static Matplotlib output, and for choosing between histogram, heatmap, and scatter workflows. If the task is really about computing counts, means, correlations, binning, groupby grids, or other precomputed statistics, route the analytic part to [../../expressions-analytics/SKILL.md](../../expressions-analytics/SKILL.md) first. If the task is about remote plot endpoints or server-side plotting, use [../../serving-remote/SKILL.md](../../serving-remote/SKILL.md).

## Plot choice

- Use `df.x.viz.histogram(...)` or `df.viz.histogram(df.x, ...)` for one-dimensional distributions and expression-based summaries.
- Use `df.viz.heatmap("x", "y", ...)` for dense 2D summaries, faceting, or overlays.
- Use `df.viz.scatter("x", "y", ...)` only for small DataFrames or explicitly bounded selections.
- Treat `df.plot1d`, `df.scatter`, and `df.plot` as compatibility shims. They may warn and are not the preferred API for new guidance.

## Static plots in scripts and CI

Use Matplotlib’s noninteractive backend and save figures explicitly. This keeps terminal checks independent from notebook rendering.

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import vaex

df = vaex.from_arrays(x=[-2, -1, 0, 1, 2], y=[4, 1, 0, 1, 4])

# Histogram via the expression accessor.
df["x"].viz.histogram(limits="minmax", shape=8, show=False, hardcopy="x_histogram.png")

# Heatmap with a saved figure.
plt.close("all")
df.viz.heatmap("x", "y", limits="minmax", shape=8, show=False, hardcopy="xy_heatmap.png")

# Scatter needs an explicit save.
plt.close("all")
df.viz.scatter("x", "y", length_limit=100)
plt.gcf().savefig("xy_scatter.png", bbox_inches="tight")
```

Guidelines:

- Prefer `hardcopy=` for `histogram` and `heatmap`.
- Use `show=False` in noninteractive scripts.
- Close figures between plots if you are generating many files.
- Keep the dataset tiny or bounded for scatter.

## Plot controls

The most commonly used controls are:

- `selection`: a named selection or a boolean expression.
- `limits`: explicit bounds, `'minmax'`, or a percentile-style bound such as `'99%'`.
- `shape`: bin count for histogram/heatmap grids.
- `what`: the statistic to render, usually one of `count(*)`, `mean(x)`, `sum(x)`, `std(x)`, `correlation(a, b)`.
- `f`: visual transform such as `'identity'`, `'log'`, `'log10'`, or `'log1p'`.
- `normalize_axis`: chooses the axis used for normalization when rendering multi-panel plots.

If `what` does not parse, or the expression is not in `function(argument)` form, treat it as a troubleshooting case rather than trying to force Matplotlib to recover.

## Multi-panel layouts

Vaex’s plotting API accepts list-based layouts and facet-like strings.

- Multiple x/y pairs create multiple panels: `df.viz.heatmap([["x", "y"], ["x", "z"]], ...)`.
- A list of `what` values creates columns or rows of statistics: `what=["count(*)", "mean(vx)"]`.
- A third axis can be sliced with `z="FeH:-3,1,5"`.
- Facets use the `name:low,high,count` form, such as `facet="energy:-3,1,8"`.
- The `visual` mapping can move `row`, `column`, `layer`, `fade`, `what`, or `subspace` between plot dimensions.
- `wrap_columns` keeps wide grids readable.

A few practical examples:

```python
# Two panels, one per axis pair.
df.viz.heatmap([["x", "y"], ["x", "z"]], limits="99%")

# Different statistics for the same axes.
df.viz.heatmap("x", "y", what=["count(*)", "mean(vx)", "correlation(vy, vz)"])

# Slice through a third axis.
df.viz.heatmap("Lz", "E", z="FeH:-3,1,5", visual=dict(row="z"), wrap_columns=3)
```

## Selection and scatter guidance

Use `selection` when the same DataFrame needs multiple views without mutating the underlying object. If the row count is large, switch to an aggregated histogram or heatmap instead of forcing a scatter plot.

Typical patterns:

```python
# Named selection.
df.select(df.x >= 0, name="nonnegative")
df.viz.scatter("x", "y", selection="nonnegative", length_limit=100)

# Boolean selection expression.
df.viz.heatmap("x", "y", selection="(x >= 0) & (y >= 0)")
```

If scatter raises the length-limit error, either narrow the selection or switch to an aggregated visualization. This is a display choice, not a signal to materialize the full table.

## Keep presentation separate from computation

A plot is the final rendering step, not the place to reimplement analytics. When you need custom grids, precomputed statistics, or joins behind a visualization, route that work to [../../expressions-analytics/SKILL.md](../../expressions-analytics/SKILL.md) and hand this sub-skill the ready-to-render result.
