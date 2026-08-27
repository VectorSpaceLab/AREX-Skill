# Trend, Radar, and Heatmap Troubleshooting

Use this guide when a trend, radar, heatmap, or mixed comparison figure fails validation, produces unreadable labels, or exports incorrectly.

## Shape and label validation failures

### `values shape does not match labels`

Symptoms:

- A series disappears or is truncated.
- The radar polygon uses the wrong number of spokes.
- Heatmap annotations are shifted into the wrong cells.

Fix:

1. Convert incoming data to `np.asarray(..., dtype=float)` before plotting.
2. Check the row/column convention explicitly in code comments.
3. Confirm the first axis matches method/series/row count and the second axis matches x/spoke/column count.
4. If the data were transposed, fix the transpose in the plotting layer rather than relying on accidental broadcasting.
5. Validate labels before plotting: `len(series_labels)`, `len(x_labels)`, `len(spokes)`, `len(row_labels)`, and `len(col_labels)` must match the array shape.

### Event labels do not land on the curve

Symptoms:

- Arrows point to the wrong month or fall between x positions.
- Event labels overlap the lines or appear outside the data region.

Fix:

- Validate that event x positions exist in the plotted x labels.
- If the x axis is categorical, map labels to integer positions once and reuse that mapping for both the line and the annotation.
- Place the arrow tip on a reference curve such as the maximum cumulative value at the event x position.
- Stagger the text y positions; do not place every label at the same height.
- Increase the top margin after adding annotations.

### Radar spokes are misaligned

Symptoms:

- Polygons seem rotated or a method value appears on the wrong spoke.
- Tick labels do not match the spoke order.

Fix:

1. Print or log the spoke order before plotting.
2. Ensure `values[:, i]`, `spoke_ranges[i]`, and `spoke_ticks[i]` all refer to the same spoke.
3. Use closed angle arrays only after the data are validated.
4. Keep the first spoke at a fixed polar zero location and rotate labels only if the entire figure is updated consistently.

### Radar polygons are not closed

Symptoms:

- The last edge does not return to the first spoke.
- The filled region has an obvious gap.

Fix:

- Append the first angle and the first normalized value to the end of each polygon before plotting.
- Reuse the same closed arrays for the line and fill calls.
- If you draw a contour overlay, close those polygons too.

### Heatmap annotations are shifted

Symptoms:

- Text appears between cells.
- Row/column labels line up with the wrong axis.

Fix:

- For `imshow`, annotate at integer centers `(col + 0.5, row + 0.5)` or use the same origin convention consistently.
- For `pcolormesh` or seaborn-style axes, follow the library’s cell-center convention and do not mix coordinate systems.
- Confirm the matrix is not accidentally transposed after the labels are built.

## Scale and normalization failures

### Radar normalization compresses everything

Symptoms:

- All methods look nearly identical.
- The outermost polygon is clipped at the same radius.

Fix:

- Verify each spoke range has a meaningful span.
- If a spoke range is too narrow or reversed accidentally, correct it before normalizing.
- Consider using a wider display radius interval for readability, but keep the mapping consistent across all methods.
- For lower-is-better metrics, invert the metric or reverse the intended display range on purpose; do not mix the two approaches.

### Heatmap colors are all too dark or too light

Fix:

- Check `vmin`/`vmax` and whether the data are all clustered near one end of the scale.
- Use a centered norm when the matrix contains positive and negative values around zero.
- For count matrices, clamp the maximum to a meaningful venue-specific upper bound instead of an automatic global maximum when a few outliers flatten the display.

### Trend lines look flat after cumulative conversion

Fix:

- Confirm whether the plotted data should be raw values or cumulative values.
- If increments are already cumulative, do not call `cumsum` again.
- Tighten the y-limits around the plotted range so the trend is visible without hiding the baseline.

## Annotation readability failures

### Heatmap text is unreadable

Cause: annotation color does not contrast with the cell fill.

Fix:

- Derive the text color from the rendered RGBA color, not from the raw numeric threshold alone.
- Use black text on light cells and white text on dark cells.
- Reduce annotation font size slightly before shrinking axis labels.
- If the cell grid is dense, remove some annotations and keep only summary cells or diagonal cells.

### Trend annotations collide with the legend

Fix:

- Move the legend into a separate axis or outside the data region.
- Put event labels above the plotted lines, not inside the legend box area.
- Reorder the axis so the legend is drawn after the annotation positions are finalized.

### Radar spoke labels overlap

Fix:

- Shorten the labels with line breaks.
- Increase the figure width or outer margin.
- Reduce the number of radial tick labels shown per spoke.
- Keep labels outside the plotting radius and avoid placing a second text ring too close to the first.

## Optional package and TeX failures

### `RuntimeError: Failed to process string with tex`

Cause: `--use-tex` was requested but LaTeX is not available.

Fix:

- Re-run without `--use-tex` for a portable default.
- If TeX is required, install and verify LaTeX outside the script, then rerun.
- Avoid full TeX macros when the default path uses matplotlib mathtext.

### Matplotlib warns about missing fonts

Fix:

- Use a portable sans-serif fallback such as DejaVu Sans.
- Avoid hard-coding a font that may not exist on the target machine.
- Re-run layout after changing font family or font size.

## Export and file failures

### Output file is missing or empty

Fix:

1. Confirm the output parent directory is created before saving.
2. Save every requested format from the same finalized figure object.
3. Check that `plt.close(fig)` happens only after the saves succeed.
4. Verify the selected file extensions are supported by matplotlib.

### A requested format is unsupported

Fix:

- Use common formats such as `png`, `pdf`, or `svg`.
- Normalize the `--formats` value by splitting on commas and stripping whitespace.
- Reject empty format tokens rather than silently skipping them.

### Existing outputs are overwritten unintentionally

Fix:

- Choose a fresh output basename.
- Use a temporary output directory for experiments.
- Do not make the script delete files automatically.

## When to revise the design

If the troubleshooting path shows that the requested figure is not actually a trend, radar, or heatmap figure, route to the more appropriate sub-skill instead of patching the template beyond recognition.
