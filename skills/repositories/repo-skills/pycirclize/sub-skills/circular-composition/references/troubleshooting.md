# Circular composition troubleshooting

Use the smallest reproducible in-memory layout first. Keep the original input
and the exception text; fix the configuration at the boundary instead of
bypassing validation or reaching into private implementation state.

## Constructor and coordinate failures

### `start`/`end` raises `ValueError`

The constructor requires `-360 <= start < end <= 360` and an angular span no
larger than 360 degrees. Examples such as `start=-10, end=360` span 370 degrees,
`start=0, end=-90` reverses the interval, and values outside the bounds are
invalid. Replace them with a bounded increasing interval, for example
`start=-270, end=30` for a full 300-degree layout. Do not normalize the values
manually if that changes the intended orientation; choose the intended visible
arc explicitly.

### Space sequence has an invalid length

With `n` sectors, `space=[...]` needs `n` values when `endspace=True` and
`n-1` values when `endspace=False`. A scalar applies uniformly. Check the
`endspace` choice before changing list length. Also ensure total space is less
than the selected angular span; otherwise no positive sector region remains.

### Tuple range is invalid or positions fail

A tuple/list sector range must have `start < end`. For a tuple such as
`{"chr1": (100, 140)}`, `link`, sector methods, and track methods expect x
coordinates between 100 and 140, not 0 and 40 and not global degrees. If a
coordinate falls outside this interval, pyCirclize raises a `ValueError` from
sector range validation. Check `sector.start` and `sector.end` before making a
link or label. Only use `ignore_range_error` on the lower-level sector text or
coordinate conversion APIs when the deliberate out-of-range annotation is
understood; it is not a fix for malformed data.

### Anti-clockwise endpoint appears reversed

`sector2clockwise={"B": False}` reverses coordinate-to-radian mapping for
sector B. Do not reverse its x values a second time. For links, retain each
endpoint in the source sector's public coordinate space, inspect both
`clockwise` flags, and render a small test with `direction=0`, `1`, `-1`, and
`2` as needed. If a ribbon twists undesirably, try `allow_twist=False`; if the
relationship itself is directional, set `direction` explicitly and verify the
arrow visually.

## Lookup and lifecycle failures

### Sector lookup fails

`circos.get_sector(name)` raises `ValueError` when the name is absent. Inspect
`[sector.name for sector in circos.sectors]`; preserve the original mapping keys
rather than coercing names to an assumed case or order. The same failure can
surface when `link` or `link_line` references an unknown sector.

### `circos.ax` is unavailable

The `ax` property is populated only by `plotfig()`. Build all queued content,
then call `fig = circos.plotfig()` before using `circos.ax`, adding legends, or
calling normal Matplotlib methods. There is no need to force an axis early.

### `plotfig(ax=...)` rejects the axis

The supplied object must be a Matplotlib `PolarAxes`, created with
`fig.add_subplot(..., projection="polar")`. A normal Cartesian `Axes` is
rejected. If composing a mixed Figure, keep a dedicated polar subplot for
Circos and use other axes for non-polar content.

### Repeated `plotfig()` behaves unexpectedly

Treat one `Circos` instance as a composition to render once for a stable
workflow. If you need multiple output variants, construct separate instances
or deliberately manage the returned Figure/axes. For a caller-owned axis,
render into that axis and save the owner Figure after all edits.

## Export and Matplotlib failures

### Legend or custom annotation is missing

`circos.savefig()` calls `plotfig()` and writes immediately; it is not a hook
for later Matplotlib edits. For legends, custom annotations, multiple legends,
subplots, or user-defined axes:

1. call `fig = circos.plotfig(...)`;
2. add edits through `circos.ax` or the returned Figure;
3. call `fig.savefig(...)` yourself.

Retain the Figure reference. `savefig()` normally clears and closes its
internal Figure after writing.

### Output is empty or no file is observed

Use a writable, explicit output path and call the export after rendering. For
`savefig`, check `Path(output).exists()` and a nonzero size. For `Figure.savefig`,
use the returned Figure and avoid closing it before saving. In a headless
runtime, select the `Agg` backend before importing `matplotlib.pyplot`.

### Colorbar fails or is misplaced

`bounds` are parent-axes inset coordinates `(x, y, width, height)`, not data
coordinates or degrees. `orientation` must be `vertical` or `horizontal`.
Keep `vmin < vmax`, use a valid Matplotlib colormap, and ensure the bounds leave
room in the Figure. A colorbar does not automatically infer or normalize a
track's data; use the same `vmin`/`vmax` and cmap contract as the plot.

### Tooltip warning in a static or non-Jupyter run

Tooltip support is optional and requires `ipympl` plus an interactive Python
runtime. Do not pass `tooltip=True` for Agg/static export. If interactive
behavior is required, install the `tooltip` extra and call it in a live
Jupyter-compatible kernel; a warning that tooltip enabling failed does not
indicate that core static composition is broken.

## Safe recovery checklist

1. Confirm the installed package reports version 1.10.1 and that the base
   imports work.
2. Reduce to two or three in-memory sectors with scalar spaces.
3. Verify ranges and names through public properties and `get_sector()`.
4. Add one primitive or link at a time, keeping endpoints in sector coordinates.
5. Render with Agg through `plotfig()` and inspect the Figure before adding
   custom legends/colorbars.
6. Export to a new explicit path; never make a bundled script overwrite an
   existing caller file or fetch data from the network.

## Known limitations

- Static verification does not prove interactive tooltip behavior; that path
  needs `ipympl` and a live notebook kernel.
- Visual aesthetics of arrows, twisted links, legends, and colorbar placement
  require human or image-level review beyond file existence.
- The public API exposes composition lifecycle behavior, but exact Matplotlib
  rendering can vary with the installed Matplotlib version.
