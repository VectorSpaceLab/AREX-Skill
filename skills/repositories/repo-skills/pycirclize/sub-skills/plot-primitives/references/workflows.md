# Plotting workflows

These recipes assume a `Circos` object has already been created by the
composition workflow. They use only public `Sector`/`Track` methods and local
in-memory data.

## 1. Establish a track and coordinate contract

```python
from pycirclize import Circos

circos = Circos({"sample": 20}, start=0, end=270)
sector = circos.get_sector("sample")
track = sector.add_track((70, 100), r_pad_ratio=0.1, name="signal")
```

Record the following before plotting:

- `x_min, x_max = sector.start, sector.end`; every x passed to a primitive
  must lie in that interval unless it is an intentionally external label or
  tick.
- `r_lim` is a radius allocation, not a y data range. Data methods map y into
  `track.r_plot_lim`; padding is therefore part of the visible data contract.
- Choose a shared `vmin, vmax` for all line/scatter/bar/fill calls that should
  be visually comparable. A method's omitted `vmax` is inferred independently
  and can make identical values occupy different radial heights.
- Use `track.x_to_rad(x)` only to inspect or integrate with custom Matplotlib
  code. Do not feed radians into methods whose signatures say `x`.

## 2. Compose primitives in a stable order

A useful local order is axis/background, grid and ticks, data marks, then
labels and annotations:

```python
import numpy as np

track.axis(fc="none", ec="0.5", lw=0.5)
track.grid(y_grid_num=4, x_grid_interval=5, color="0.8", lw=0.4)
track.xticks_by_interval(5, label_orientation="vertical")
track.yticks([0, 0.5, 1.0], ["0", ".5", "1"], vmin=0, vmax=1)

x = np.linspace(track.start + 1, track.end - 1, 5)
y = np.array([0.1, 0.7, 0.4, 0.9, 0.3])
track.line(x, y, vmin=0, vmax=1, color="tab:blue")
track.scatter(x, y, vmin=0, vmax=1, c="tab:orange", s=16)
track.fill_between(x, y, 0.2, vmin=0, vmax=1, fc="tab:blue", alpha=0.15)
track.text("signal", r=track.r_center, size=8)
```

`axis()` and `grid()` are optional. Add them before data when their z-order
should stay behind marks. All style kwargs are passed to the corresponding
Matplotlib operation; use `line_kws`, `text_kws`, `rect_kws`, or `bar_kws`
when the method exposes a nested style dictionary.

## 3. Compare bars, stacked bars, and heatmaps

Use a single explicit scale for mixed numeric primitives:

```python
values = np.array([0.2, 0.5, 0.8, 0.4])
x = np.arange(track.start + 2, track.start + 10, 2)
track.bar(x, values, width=1.2, vmin=0, vmax=1, fc="tomato", ec="black")
track.bar(x, 1 - values, width=1.2, bottom=values,
          vmin=0, vmax=1, fc="skyblue", ec="black")
track.heatmap([[0.0, 0.3, 0.7, 1.0]], vmin=0, vmax=1,
              cmap="viridis", show_value=True,
              rect_kws={"ec": "white", "lw": 0.3})
```

For `stacked_bar`, pass a pandas `DataFrame` or `StackedBarTable` with rows
corresponding to x positions. For `stacked_barh`, the table rows are laid out
as radial bands and the sector x range represents the row totals; prepare the
sector range to match those totals. The parser/data route owns matrix/table
semantics and color assignment; this route owns the final drawing call.

## 4. Add biological marks after coordinate validation

Once the genomics workflow has parsed and validated Biopython features, call:

```python
track.genomic_features(
    features,
    plotstyle="arrow",
    r_lim=(90, 95),
    facecolor_handler=lambda feature: "salmon"
    if feature.location.strand == 1 else "skyblue",
    ec="none",
)
```

For generic directional intervals, `track.arrow(start, end, ...)` is enough.
For feature-derived labels, compute a numeric midpoint in the feature's own
coordinate system and call `track.annotate(midpoint, label, ...)`. Do not infer
feature semantics in this sub-skill; route malformed locations, strands,
qualifiers, and tree data to `genomics-and-trees`.

## 5. Use annotations deliberately

`annotate` queues labels for automatic overlap adjustment at render time. Keep
labels short, set a bounded `min_r`/`max_r` when the outer margin is constrained,
and customize with copied dictionaries:

```python
for x, label in zip([2, 3, 4], ["alpha", "beta", "gamma"], strict=True):
    track.annotate(
        x, label, min_r=100, max_r=108, shorten=12,
        line_kws={"color": "0.4", "lw": 0.4},
        text_kws={"color": "0.2"},
    )
```

Crowded labels can exceed the available radial margin even after adjustment.
Reduce label count/size, shorten text, spread x positions, or configure the
package annotation settings consciously; do not assume automatic adjustment
makes every label legible.

## 6. Render and export with Agg

The primitive methods defer drawing. Render through the parent object and use a
caller-owned output path:

```python
import matplotlib
matplotlib.use("Agg")

fig = circos.plotfig()
fig.savefig("plot.png", dpi=120, bbox_inches="tight")
# or circos.savefig("plot.png") for the package's normal static export
```

In a smoke or evaluation script, use deterministic arrays and a fresh output
path, assert that the PNG exists and is non-empty, and close the figure. Do not
load network images, source-repository fixtures, or example assets. The bundled
script follows this policy and refuses to overwrite an existing output file.
