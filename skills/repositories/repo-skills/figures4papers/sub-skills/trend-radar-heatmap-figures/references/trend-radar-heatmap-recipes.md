# Trend, Radar, and Heatmap Recipes

This reference is a self-contained operating guide for trend panels, event-annotated cumulative time series, radar/polar comparisons, heatmaps, matrix panels, colorbars, annotations, and shared legends. Use it with user-provided data or the bundled template script; do not depend on historical checkout files or external datasets.

## Shared plotting contract

- Use a non-interactive matplotlib backend in unattended scripts before importing `pyplot`.
- Keep data explicit in the script, read from a user-supplied table only when the task explicitly provides one, and never require private source-tree paths.
- Validate shapes before drawing: numeric arrays must be finite, label counts must match array dimensions, and every plotted method/category must have a readable label.
- Prefer portable sans-serif fonts and non-TeX rendering. Enable TeX only when the runtime explicitly has LaTeX and exact TeX rendering is required.
- Use deterministic outputs: create the parent output directory, save every requested format from the same finalized figure, and close the figure after saving.
- Use semantic colors consistently: dark blue for a key method or primary trend, green for improvements, red/pink for contrasts, and neutral gray for references.

## Data contracts

### Event-annotated trend panel

Use this contract for line, sweep, monthly-count, cumulative-count, or event timeline figures.

```python
trend = {
    "x_labels": ["2023-01", "2023-02", "2023-03", "2023-04"],
    "series_labels": ["Benchmark", "Methodology"],
    "values": [[1, 2, 3, 4], [0, 1, 2, 5]],  # shape: (n_series, n_x)
    "cumulative": True,
    "events": [
        {"x": "2023-02", "label": "Model A"},
        {"x": "2023-04", "label": "Dataset release"},
    ],
}
```

Validation rules:

- `values` must be a finite numeric 2D array with shape `(len(series_labels), len(x_labels))`.
- If `cumulative=True`, increments should normally be non-negative; negative corrections must be intentional and captioned.
- Event positions must exist in `x_labels` or be mapped to the nearest plotted x value by a documented policy.
- Date-like labels should sort chronologically. For monthly trends, prefer zero-padded `YYYY-MM` labels.
- Each trend line should use a visible marker or line style when the palette alone is not enough.

### Radar or polar benchmark comparison

Use this contract when spokes have different natural scales.

```python
radar = {
    "methods": ["Ours", "Baseline A", "Baseline B"],
    "spokes": ["Model 1\nAccuracy", "Model 2\nF1", "Model 3\nLatency ↓"],
    "values": [[88.2, 71.0, 34.0], [84.0, 66.0, 52.0], [80.0, 62.0, 61.0]],
    "spoke_ranges": [(75, 90), (55, 75), (70, 25)],
    "spoke_ticks": [[75, 80, 85, 90], [55, 65, 75], [70, 55, 40, 25]],
}
```

Validation rules:

- `values` must have shape `(len(methods), len(spokes))`.
- `len(spoke_ranges) == len(spokes)` and each range must have nonzero span.
- A decreasing range such as `(70, 25)` is allowed for lower-is-better metrics; normalization should treat the first value as the inner/low-performance reference and the second value as the outer/high-performance reference only if that is the intended direction. Otherwise reorder the range before plotting.
- Every method polygon must be closed by appending the first angle and first normalized value at the end.
- Do not interpolate between spokes beyond the straight polygon edge; each vertex should represent a real measured or synthetic value.
- If a benchmark family uses shared tick values across multiple spokes, label those ticks per spoke rather than relying on a single global radial axis.

Per-spoke normalization formula:

```python
frac = (value - lo) / (hi - lo)
frac = clip(frac, 0.0, 1.0)
display_radius = display_min + frac * (display_max - display_min)
```

For lower-is-better metrics, either pass `lo` and `hi` in display-performance order or explicitly invert the metric before applying the formula. Keep the policy visible in code comments.

### Heatmap or matrix panel

Use this contract for count matrices, performance grids, correlations, confusion-like summaries, and method-by-metric tables.

```python
heatmap = {
    "matrix": [[12, 4, 0], [3, 9, 2], [1, 5, 15]],  # shape: (n_rows, n_cols)
    "row_labels": ["Clinical", "Patient", "Education"],
    "col_labels": ["Eval", "Expert", "Trial"],
    "annot_format": "{:.0f}",
    "cbar_label": "Count",
}
```

Validation rules:

- `matrix` must be a finite numeric 2D array.
- `len(row_labels) == matrix.shape[0]` and `len(col_labels) == matrix.shape[1]`.
- If annotation text is enabled, choose text color from the rendered cell color, not from the raw value alone.
- For diverging matrices with meaningful zero, set symmetric limits or use a centered normalization.
- For count matrices, use integer formatting and a sequential colormap; for signed improvements, use a diverging colormap and include units in the colorbar label.

Text contrast rule:

```python
rgba = cmap(norm(value))
luminance = 0.2126 * rgba[0] + 0.7152 * rgba[1] + 0.0722 * rgba[2]
text_color = "black" if luminance > 0.55 else "white"
```

## Recipes

### Cumulative trend with event arrows

1. Convert increments to cumulative values with `np.cumsum(values, axis=1)` when cumulative storytelling is requested.
2. Plot each series as a line with a marker and optional translucent fill under the curve.
3. Compute a reference y curve for event arrows, often the maximum cumulative value across series at each x position.
4. For each event, validate that its x label exists, then annotate with an arrow from a staggered text position to the reference curve.
5. Alternate or explicitly set vertical offsets so event labels do not collide.
6. Show only a readable subset of dense monthly ticks, such as every third or sixth label.
7. Reserve enough top margin after annotations; do not let `tight_layout` clip arrows.

### Sweep curves with shared legend axis

1. Use one axis per metric or condition when each y-axis has its own units.
2. Reuse colors and markers for the same method across axes.
3. Put the legend in the last axis or outside the axes when more than two series are plotted.
4. Use dynamic y-limits per metric and `MaxNLocator` for 4-6 readable ticks.
5. If x is ordered but nonuniform, plot at the actual numeric x values and set ticks to those values.

### Radar comparison with per-spoke ticks

1. Build `angles = np.linspace(0, 2*pi, n_spokes, endpoint=False)` and a closed copy with the first angle appended.
2. Normalize every method value independently per spoke using that spoke's range.
3. Close every method polygon by appending the first normalized value.
4. Draw custom spokes and contour polygons because a single polar radial axis cannot represent different natural units per spoke.
5. Add per-spoke tick labels using the natural tick values from `spoke_ticks`; skip the innermost tick when labels become crowded.
6. Put spoke labels outside the outer radius and increase figure margins for multi-line labels.
7. Use low-alpha fills and visible vertex markers so readers can distinguish real data points from polygon edges.

### Heatmap with readable annotations

1. Plot with `imshow` or a seaborn heatmap equivalent after validating matrix dimensions.
2. Use a sequential colormap for nonnegative counts/scores and a diverging colormap for signed differences.
3. Annotate each cell with a short numeric label; derive black/white text color from the displayed RGBA color.
4. Rotate x tick labels only when the label text is too long for horizontal placement. Prefer manual line breaks over steep rotations in paper figures.
5. Keep colorbar ticks sparse and include a unit-bearing label.
6. When row/column totals help the story, include them in tick labels or add a separate summary row/column; make sure totals do not change the plotted matrix shape unexpectedly.

### Mixed trend-heatmap or matrix layout

- Use `GridSpec` or subplots with explicit width ratios when combining a line panel with a heatmap or a legend-only axis.
- Keep one visual job per axis: data axes show data, legend axes show legends, colorbar axes show color scales.
- Match typography across axes, but allow smaller heatmap annotation text than axis labels.
- Align panel titles and use short caption-ready axis labels rather than long prose in the figure itself.

## Export checklist

Before handing off a figure script or result:

- `--help` works without reading data files or importing unavailable optional packages.
- The script can run on a headless machine using the Agg backend.
- Built-in examples are deterministic and require no network, credentials, or private paths.
- The output basename and formats are user-selectable.
- Every saved path exists and has nonzero size.
- TeX is opt-in and produces a clear error if the runtime lacks LaTeX.
- All arrays, labels, event positions, ranges, and tick lists are validated before plotting.

## Related runtime files

- [`../scripts/trend_radar_heatmap_template.py`](../scripts/trend_radar_heatmap_template.py) provides safe built-in examples for trend, radar, and heatmap figures.
- [`troubleshooting.md`](troubleshooting.md) lists fixes for validation failures, unreadable labels, radar scale problems, colorbar issues, and export problems.
