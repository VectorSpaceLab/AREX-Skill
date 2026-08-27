# Bar Comparison Recipes

This reference turns the figures4papers bar evidence into reusable operating
recipes. It is self-contained: use the schemas and snippets here with user data
or with the bundled template; do not require historical checkout files.

## Distilled source idioms

- Brainteaser-style probability panels: very wide canvases, hidden x ticks,
  method colors in a separate legend, subtype hatches, and direct numeric labels
  for dense categorical comparisons.
- CellSpliceNet-style metric panels: one panel per metric, method colors shared
  across panels, mean/std error bars, large annotations just above the cap, and
  tightened y-limits for narrow score bands.
- ImmunoStruct-style comparison bars: 3-metric rows, a final legend-only axis,
  high-DPI export, and horizontal `barh` ablations with alpha gradients.
- Cflows-style comparison rows: compact wide panels with one metric or dataset
  per axis, scientific tick formatting for small or large values, and PNG/PDF
  export from the same figure.
- RNAGenScape-style speed bars: positive throughput values on a log axis, no
  x-tick method labels, annotations above each bar, and a frameless legend.

## Data schemas

### Multi-metric vertical comparison

Use this when rows are methods and columns are metrics. `mean` and optional
`err` must both have shape `(n_methods, n_metrics)`.

```python
comparison = {
    "methods": ["Ours", "Baseline A", "Baseline B"],
    "metrics": ["AUROC", "AUPRC", "Throughput ↑"],
    "mean": [[0.91, 0.72, 1.45], [0.86, 0.61, 0.38], [0.83, 0.58, 0.22]],
    "err":  [[0.01, 0.03, 0.08], [0.02, 0.02, 0.04], [0.02, 0.03, 0.03]],
    "colors": ["#0F4D92", "#AADCA9", "#E9A6A1"],
    "metric_scales": ["linear", "linear", "log"],
}
```

Validation rules:

- `len(methods) == mean.shape[0]`.
- `len(metrics) == mean.shape[1]`.
- `err is None` or `err.shape == mean.shape`.
- `len(colors) == len(methods)` when explicit colors are supplied.
- Log-scale metrics must be strictly positive after accounting for lower error
  bounds.

### Grouped method-by-category bars

Use this for one metric across multiple conditions or datasets. A convenient
schema is `values.shape == (n_groups, n_categories)` where each group is a
method and each category is an x-axis condition.

```python
grouped = {
    "categories": ["Dataset A", "Dataset B", "Dataset C"],
    "groups": ["Ours", "Baseline A", "Baseline B"],
    "values": [[0.91, 0.87, 0.89], [0.83, 0.81, 0.78], [0.76, 0.74, 0.73]],
    "errors": [[0.02, 0.02, 0.01], [0.03, 0.02, 0.02], [0.02, 0.03, 0.02]],
}
```

Draw each category at `x = arange(n_categories)` and offset each group around
that center. Keep total cluster width near `0.75` and individual widths near
`0.75 / n_groups`.

### Horizontal ablation bars

Use this when each row is a variant or component subset. `mean` and optional
`err` must have shape `(n_ablations, n_metrics)`.

```python
ablation = {
    "components": ["Structure", "Sequence", "Transfer"],
    "codes": ["111", "110", "101", "011", "100"],
    "metrics": ["AUROC", "AUPRC"],
    "mean": [[0.91, 0.72], [0.87, 0.64], [0.86, 0.63], [0.82, 0.55], [0.78, 0.48]],
    "err":  [[0.01, 0.02], [0.02, 0.03], [0.02, 0.02], [0.02, 0.03], [0.03, 0.04]],
}
```

Decode each code by including component names where the bit is `1`. If a code
contains no selected components, label it `None`. Validate that every code has
exactly `len(components)` characters and only uses `0` or `1`.

## Recipe: wide multi-metric comparison row

1. Apply a publication style with a sans-serif fallback, top/right spines off,
   base font size 18-24, and axes linewidth 2.5-3.
2. Create `n_metrics + 1` axes in one row; reserve the last axis for the legend
   when there are many methods.
3. For each metric axis:
   - Draw `n_methods` bars at integer positions.
   - Pass `yerr=err[:, metric_idx]` when errors are available.
   - Use `capsize` between 5 and 10 and `error_kw={"capthick": 2, "elinewidth": 2}`.
   - Use `edgecolor="black"` and `linewidth=1.5-2.5` for print safety.
   - Hide method x ticks with `ax.set_xticks([])` unless there are three or
     fewer short labels.
   - Set the y-axis label to the metric name, including `↑` or `↓` when useful.
4. Capture legend handles from the first axis and draw them centered in the
   legend axis with `frameon=False`.
5. Finish with `fig.tight_layout(pad=1.5 or 2)` and save every requested format.

Use `figsize` roughly as follows:

| Metrics | Methods | Suggested figsize |
| --- | ---: | --- |
| 1 | 3-8 | `(8, 5)` to `(13, 6)` |
| 3 | 5-10 | `(24, 6)` to `(45, 12)` |
| 4 | 5-9 | `(28, 6)` to `(35, 7)` |
| 2 rows of panels | 5-8 | `(24, 10)` to `(52, 12)` |

## Recipe: true grouped bars on one axis

Use a single axis when the primary narrative is category-by-category comparison
rather than metric-by-metric comparison.

```python
x = np.arange(n_categories)
total_width = 0.78
bar_width = total_width / n_groups
offsets = (np.arange(n_groups) - (n_groups - 1) / 2) * bar_width
for group_idx, group_name in enumerate(groups):
    ax.bar(x + offsets[group_idx], values[group_idx], width=bar_width,
           yerr=None if errors is None else errors[group_idx],
           color=colors[group_idx], edgecolor="black", linewidth=1.8,
           label=group_name)
```

Keep category labels short. If category labels are long, either wrap them to two
lines or switch to horizontal bars.

## Recipe: horizontal ablation panels

1. Decode component labels before plotting; never show raw binary codes unless
   the paper explicitly defines them.
2. Make one column per metric and share the y-axis.
3. Draw `barh` rows with `xerr` when errors are available.
4. Use one semantic color with alpha increasing from incomplete variants to the
   full variant, or use a highlight color for the full model and neutral colors
   for removals.
5. Show y labels only on the first metric axis; hide repeated y ticks on the
   others.
6. Put exact values just to the right of each bar, adding the error amount to
   the x position when error bars are present.
7. Invert the y-axis when the full model or most complete variant should appear
   first.

## Legend-only axes

A legend-only axis is more robust than a crowded legend inside a data panel.
Use it when there are many methods, hatches, or long labels.

```python
handles, labels = axes[0].get_legend_handles_labels()
legend_ax.set_axis_off()
legend_ax.legend(handles, labels, loc="center", frameon=False, ncols=1)
```

For print-safe subtype encodings, create proxy patches so the legend documents
both color roles and hatch roles. A color legend explains methods; a hatch legend
explains subtypes or prompt categories.

## Annotation rules

- Vertical bars with errors: label at `height + error + pad`.
- Vertical bars without errors: label at `height + pad`, where `pad` is about
  `1-3%` of the data range.
- Horizontal bars with errors: label at `width + error + pad`.
- Inside-bar labels: use only for tall enough bars; select white text on dark
  fills and black text on light fills using luminance.
- Log bars: multiply the label position by a factor such as `1.08` instead of
  adding a linear offset.
- If labels collide with the top boundary, expand the axis limit and rerun
  layout; do not shrink labels until the data range has been fixed.

## Dynamic axis limits

For linear vertical bars:

```python
lo = min(values - errors) if errors is not None else min(values)
hi = max(values + errors) if errors is not None else max(values)
span = max(hi - lo, 1e-9)
margin = max(0.06 * span, 0.02 * abs(hi), 0.02)
ymin = 0 if lo >= 0 and lo / max(hi, 1e-9) < 0.75 else lo - margin
ymax = hi + 2 * margin
```

Guidance:

- Keep zero visible for counts, losses, runtime, and percentages when the
  absolute baseline matters.
- Tighten score-like metrics when all values are high and close together.
- Add extra top margin for annotations and error caps.
- For metrics with possible negatives, include the negative range and add a
  horizontal zero line when it aids interpretation.
- For log bars, require positive values and set limits multiplicatively.

## Print-safe colors, hatches, and edges

Recommended palette roles:

| Role | Color examples | Use |
| --- | --- | --- |
| Key/proposed | `#0F4D92`, `#3775BA` | Main method or highlighted reference |
| Improvement family | `#DDF3DE`, `#AADCA9`, `#8BCF8B` | Related positive variants |
| Contrast/baseline | `#F6CFCB`, `#E9A6A1`, `#B64342` | Alternatives or negative contrasts |
| Neutral baseline | `#CFCECE`, `#767676`, `#4D4D4D` | Background methods |
| Single callout | `#FFD700` | One annotation highlight only |

Use hatches such as `/`, `\\`, `x`, `-`, `.` only when color is not enough.
Give every hatched bar a black edge; hatches without edges often disappear in
PDF readers and grayscale print.

## Export checks

Before considering a figure ready:

- The script sets a non-interactive backend for unattended runs.
- The parent output directory is created automatically.
- PNG and PDF are written from the same figure object unless the user requests a
  different set.
- DPI is 300 for ordinary publication panels and 600 for very dense bar rows.
- Fonts use a portable sans-serif fallback; TeX is disabled unless explicitly
  requested and available.
- The script closes the figure after saving to avoid memory buildup in batches.
- Open the generated files or at least check that the expected paths exist and
  are non-empty.
