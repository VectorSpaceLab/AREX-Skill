# Plot-primitives troubleshooting

## Coordinate and range failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ValueError` from `x_to_rad`, `text`, `rect`, `arrow`, or a data method | An x/start/end value is outside the parent sector's `[start, end]` range, or a reversed/derived value escaped it | Print `sector.start`, `sector.end`, and the offending values. Clip or regenerate x in the intended interval. Use `ignore_range_error=True` only for a deliberate external label/tick. |
| A track's mark appears to float away from the axis | `r_pad_ratio` moved data into `r_plot_lim`, while the axis uses full `r_lim` | Inspect `track.r_lim` and `track.r_plot_lim`. Use `ignore_pad=True` or an explicit `r_lim` only when touching the boundary is intentional. |
| `r_lim` is rejected by `Track.rect`, `arrow`, or `genomic_features` | The explicit radial interval is not strictly inside the track allocation, or its endpoints are reversed/equal | Pass `min_r < max_r` within `track.r_lim`; remember that `r_lim` is radial geometry, not the y data scale. |
| `add_track` warns about an unexpected range or rejects a duplicate name | Radius is outside the conventional 0--100 display range, or a track name already exists | Fix the radius allocation and give each track a unique name. Do not rely on the warning as a normalization step. |
| Plot direction looks reversed | The parent sector was created anti-clockwise | Inspect `sector.clockwise` and keep x in the sector's coordinate convention. `x_to_rad` honors the direction; do not manually reverse x a second time. |

## y values, normalization, and mixed plots

| Symptom | Likely cause | Recovery |
|---|---|---|
| `value=... is not in valid range` | A y value, bar bottom, bar top, or fill boundary is outside `[vmin, vmax]` | Compute the full data extent first. Either correct the data or choose an explicit scale covering every value. For bars, check both `bottom` and `bottom + height`. |
| Two lines/heatmaps with the same values have different radial heights | One call inferred `vmax` and another used a different explicit scale | Pass the same `vmin` and `vmax` to every comparable call, including `yticks` and `heatmap`. |
| A bar or fill has unexpected height | `bottom`/`y2` were not included in the intended scale, or a scalar was broadcast | Make `bottom`/`y2` explicit arrays when comparing series and include their extrema in the chosen `vmin`/`vmax`. |
| `line` or `fill_between` has a kinked or visually chord-like segment | `arc=False` selected straight polar-coordinate interpolation | Use the default `arc=True` for a circular data path, or keep `arc=False` when the straight geometry is intentional. |
| `heatmap` raises that data is not 1-D or 2-D | The input has three or more dimensions | Reshape or reduce the data before calling `heatmap`; a 1-D input is promoted to one row. |
| Heatmap last column is misplaced or `width` is invalid | The custom cell width does not satisfy `(columns - 1) * width < end - start < columns * width` | Remove `width` for equal cells or choose a width satisfying the documented fit inequality. |

## Length, table, and tick failures

- Line, scatter, bar, and tick label lists must have matching lengths. A
  `List length is not match` error is a data-shape error, not a Matplotlib
  styling problem. Check `len(x)`, `len(y)`, `len(height)`, and labels before
  calling the method.
- `xticks_by_interval` requires a positive interval. It is safer for regular
  ticks than manually constructing a range that may include values outside the
  sector. Use `label_formatter` for units such as kb/Mb.
- `yticks(side=...)` accepts only `"left"` and `"right"`; provide an explicit
  `vmax` when the labels must share a scale with another track.
- `grid(y_grid_num=...)` requires at least two y grid lines when enabled;
  `x_grid_interval` must be positive. Set either argument to `None` to disable
  that grid direction.
- `stacked_bar`/`stacked_barh` requires a table shape and labels compatible
  with `StackedBarTable`. Route delimiter, row/column, and color-map errors to
  the data-parsers workflow; this skill only diagnoses the drawing boundary.

## Image and raster failures

- Use a real local file path or an already loaded PIL `Image.Image`. A missing
  path, unsupported format, or malformed image fails while `utils.load_image`
  is preparing the plot; check the path and open it with PIL first.
- For deterministic, offline runs, avoid URL image inputs even where the API
  accepts them. Generate a tiny PIL image in memory or use a caller-provided
  local image.
- `Sector.raster` rejects rotation values other than `None`, a number, or
  `"auto"`; its label position is only `"top"` or `"bottom"`.
- `Track.raster` requires `0 < w <= 1` and `0 < h <= 1`. Its extra kwargs are
  passed to `Axes.pcolormesh`, not `imshow`; remove image-only kwargs if the
  error names an unexpected pcolormesh argument.
- Very narrow sectors can produce a tiny raster grid after resizing. Increase
  the sector/track span or omit raster from the small smoke case rather than
  enlarging the image outside the intended plot.

## Annotation and feature failures

- `annotate` raises when `max_r < min_r`. Set both explicitly and leave enough
  radial margin beyond the data track for labels and leader lines.
- Overlap adjustment is heuristic. Crowded annotations may still overlap, may
  move outward, or may be skipped with a warning when the configured annotation
  limit is exceeded. Shorten labels, reduce `label_size`, split labels across
  tracks, or disable/adjust the package setting only after checking the figure.
- Do not pass a precomputed radian as `annotate`'s x. Convert a feature
  midpoint into the sector's x coordinate instead.
- `genomic_features` expects Biopython `SeqFeature` objects with usable
  locations. Malformed or non-integer feature locations can be skipped with a
  parse message; invalid `plotstyle` values are rejected. Validate strand and
  location in the genomics route before drawing.

## Export and optional interaction

- A primitive call only queues work. If the PNG is empty or no marks appear,
  call `circos.plotfig()` or `circos.savefig()` after all primitive calls and
  before closing the figure.
- Select `matplotlib.use("Agg")` before importing `pyplot` for headless export.
  If a GUI/backend error appears, check backend selection rather than changing
  pyCirclize coordinates.
- Static PNG export does not require `ipympl`. Tooltip metadata may be attached
  to supported rectangles, arrows, bars, or scatter collections, but interactive
  display is an optional Jupyter concern and is not a core smoke gate.
