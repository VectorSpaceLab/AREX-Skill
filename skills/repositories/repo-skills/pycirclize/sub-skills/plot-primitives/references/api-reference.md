# Sector and Track API reference

Verified against pyCirclize **1.10.1** on Python 3.11. The package requires
Python >=3.10 and uses Matplotlib, NumPy, pandas, and Biopython for the
relevant plotting paths. `ipympl` is optional for the tooltip/Jupyter path; it
is not needed for static plotting or Agg export.

## Coordinate model and object properties

A `Sector` has an x-coordinate interval (`start`, `end`, `size`, `center`) and a
polar interval (`rad_lim`, `rad_size`, `deg_lim`, `deg_size`). A `Track`
inherits the sector's x and angular coordinates and adds a radius interval:

```python
track = sector.add_track(
    r_lim=(70, 100),
    r_pad_ratio=0.1,
    name="signal",                 # optional; defaults to TrackNN
)
```

- `r_lim` is the track's allocated radius range, conventionally 0--100.
  Values outside that convention produce a warning at `add_track`, not an
  automatic correction.
- `r_pad_ratio` is a fraction of the track thickness. With `(70, 100)` and
  `0.1`, data plotting uses `track.r_plot_lim == (71.5, 98.5)` while axis
  outlines can use the full `r_lim`.
- `r_plot_lim` and `r_plot_size` are the default data area after padding;
  `r_lim`, `r_size`, and `r_center` describe the allocated track.
- `track.x_to_rad(x, ignore_range_error=False)` delegates to the parent sector.
  It maps the sector's x interval to its angular interval and honors a
  sector's clockwise/anti-clockwise direction. It raises `ValueError` for x
  outside the sector, apart from a small internal floating-point tolerance.
- `ignore_range_error=True` is intended for labels or ticks deliberately
  placed just outside a track, not for data silently falling outside its
  sector.

`Sector` owns `add_track`, `axis`, `text`, `line`, `rect`, and experimental
`raster` methods. `Track` owns the data and annotation methods below. Both
objects expose `patches` and deferred `plot_funcs`; callers normally should
not mutate those internals directly.

## Sector primitives

The verified public signatures are:

```python
Sector.add_track(r_lim, *, r_pad_ratio=0, name=None)
Sector.x_to_rad(x, ignore_range_error=False)
Sector.axis(**kwargs)
Sector.text(text, x=None, r=105, *, adjust_rotation=True,
            orientation="horizontal", ignore_range_error=False, **kwargs)
Sector.line(*, r, start=None, end=None, arc=True, **kwargs)
Sector.rect(start=None, end=None, r_lim=None, tooltip=None, **kwargs)
Sector.raster(img, *, size=0.05, x=None, r=105, rotation=None,
              border_width=0, label=None, label_pos="bottom",
              label_margin=0.1, imshow_kws=None, text_kws=None)
```

Use sector methods for marks spanning a sector or for labels outside a track.
`Sector.line` accepts a scalar radius or a `(r_start, r_end)` radial span;
`start` and `end` default to the sector bounds. `Sector.rect` defaults to the
whole sector and full radius range when omitted. Sector patch styling includes
`fc`/`facecolor`, `ec`/`edgecolor`, `lw`/`linewidth`, `ls`, `alpha`, `hatch`,
and other Matplotlib patch properties.

`Sector.raster` accepts a local image path or a PIL image and is experimental.
Use `rotation=None`, a numeric angle, or `"auto"`; `label_pos` is only
`"top"` or `"bottom"`. Prefer a local PIL image for reproducible, no-network
workflows.

## Track annotation and layout primitives

```python
Track.axis(**kwargs)
Track.text(text, x=None, r=None, *, adjust_rotation=True,
           orientation="horizontal", ignore_range_error=False, **kwargs)
Track.rect(start, end, *, r_lim=None, ignore_pad=False,
           tooltip=None, **kwargs)
Track.arrow(start, end, *, r_lim=None, head_length=2,
            shaft_ratio=0.5, tooltip=None, **kwargs)
Track.annotate(x, label, *, min_r=None, max_r=None, label_size=8,
               shorten=20, line_kws=None, text_kws=None)
```

- `Track.axis()` draws a full track outline. `Track.rect()` defaults to
  `r_plot_lim`; set `ignore_pad=True` to use the full `r_lim`, or pass an
  explicit `r_lim` within the track allocation.
- `text` defaults to the track center. `adjust_rotation` uses the polar
  location; `orientation` is `"horizontal"` or `"vertical"` for the automatic
  label calculation. Any Matplotlib text kwargs can be passed through.
- `arrow` uses `head_length` in degree units and `shaft_ratio` in `[0, 1]`.
  Reversing `start` and `end` reverses the arrow direction.
- `annotate` draws a leader line and label and participates in the package's
  automatic overlap adjustment. `min_r` defaults to the track's outer edge
  and `max_r` defaults to `min_r + 5`; `shorten=None` preserves long labels.
  `line_kws` are patch/arrow properties and `text_kws` are text properties.

Ticks and grids:

```python
Track.xticks(x, labels=None, *, tick_length=2, outer=True,
             show_bottom_line=False, label_size=8, label_margin=0.5,
             label_orientation="horizontal", line_kws=None, text_kws=None)
Track.xticks_by_interval(interval, *, tick_length=2, outer=True,
                         show_bottom_line=False, show_label=True,
                         show_endlabel=True, label_size=8, label_margin=0.5,
                         label_orientation="horizontal", label_formatter=None,
                         line_kws=None, text_kws=None)
Track.yticks(y, labels=None, *, vmin=0, vmax=None, side="right",
             tick_length=1, label_size=8, label_margin=0.5,
             line_kws=None, text_kws=None)
Track.grid(y_grid_num=6, x_grid_interval=None, **kwargs)
```

`xticks` positions are x coordinates; `outer=False` puts ticks inside the
track. `xticks_by_interval` is preferable for regular positions and can format
labels with a callable. `yticks` values are normalized to the track's radial
plot area using `vmin`/`vmax`; `side` must be `"left"` or `"right"`. `grid`
requires `y_grid_num >= 2` when enabled and a positive x interval.

## Numeric data primitives

All numeric arrays are expected to have matching lengths where applicable.
Each method converts x to radians and maps y/value values into
`track.r_plot_lim`:

```python
Track.line(x, y, *, vmin=0, vmax=None, arc=True, **kwargs)
Track.scatter(x, y, *, vmin=0, vmax=None, tooltip=None, **kwargs)
Track.bar(x, height, width=0.8, bottom=0, align="center", *,
          vmin=0, vmax=None, **kwargs)
Track.fill_between(x, y1, y2=0, *, vmin=0, vmax=None, arc=True, **kwargs)
```

- If `vmax` is omitted, line/scatter use `max(y)`; bars use the maximum of
  `height + bottom`; `fill_between` derives bounds from both curves. For
  comparable tracks or mixed primitive plots, always pass the same explicit
  `vmin` and `vmax` to every call.
- Values must be within the inclusive `[vmin, vmax]` range (with a small
  internal tolerance). Bar `bottom` and its top are both checked.
- `arc=True` interpolates sloped lines/fills along the circular arc; use
  `arc=False` for a straight polar-coordinate segment where that is the
  intended visual geometry.
- `width` is the x-width of bars; `align` is Matplotlib's `"center"` or
  `"edge"`. Matplotlib line, scatter, bar, and fill kwargs are passed through.
  Tooltip labels for scatter are optional and require the package's optional
  tooltip configuration to be enabled to display interactively.

## Table, matrix-like, image, and feature method families

```python
Track.stacked_bar(table_data, *, delimiter="\t", width=0.6,
                  cmap="tab10", vmax=None, show_label=True,
                  label_pos="bottom", label_margin=2,
                  bar_kws=None, label_kws=None)
Track.stacked_barh(table_data, *, delimiter="\t", width=0.6,
                   cmap="tab10", bar_kws=None)
Track.heatmap(data, *, vmin=None, vmax=None, start=None, end=None,
              width=None, cmap="bwr", show_value=False,
              rect_kws=None, text_kws=None)
Track.raster(img, *, w=1.0, h=1.0, rotate=True, **kwargs)
Track.genomic_features(features, *, plotstyle="box", r_lim=None,
                       facecolor_handler=None, **kwargs)
```

- `stacked_bar` accepts a local table path, pandas `DataFrame`, or
  `StackedBarTable`; `cmap` may be a Matplotlib colormap name or a
  column-name-to-color mapping. `stacked_barh` uses rows as radial bands and
  is useful when the sector x range represents totals.
- `heatmap` accepts a 1-D or 2-D numeric array. A 1-D array becomes one row;
  higher dimensions are invalid. Defaults span the track's x range and padded
  radial range. Use explicit `vmin`/`vmax` when heatmaps are compared with
  other plots. `width` is only valid when it satisfies the documented
  last-column fit condition. `rect_kws` and `text_kws` are copied per call.
- `Track.raster` accepts a local image path or PIL image and maps it with
  `pcolormesh`; `w` and `h` must be in `(0, 1]`. It can rotate lower tracks by
  180 degrees. Pass only appropriate `pcolormesh` kwargs.
- `genomic_features` accepts Biopython `SeqFeature` or a sequence of them,
  uses feature locations and strand to choose box/arrow direction, and
  defaults to `r_plot_lim`. `plotstyle` is `"box"` or `"arrow"`; validate
  biological feature coordinates before calling it. Feature semantics and
  tree plotting belong to the genomics route.

The style dictionaries and `**kwargs` are deliberately thin wrappers around
Matplotlib. Keep one convention within a figure (`fc` versus `facecolor`,
`ec` versus `edgecolor`, `lw`, `ls`, color maps, marker arguments) and avoid
passing arguments from one primitive family to another without checking its
underlying Matplotlib call.

## Rendering and output

Primitive calls queue patches and plotting callbacks. They do not produce a
file until the parent is rendered:

```python
fig = circos.plotfig()       # optionally pass a user-created polar Axes
circos.savefig("plot.png")  # static export; parent owns the lifecycle
# or: fig.savefig("plot.png", dpi=150)
```

Use `matplotlib.use("Agg")` before importing `pyplot` in headless checks. The
verified preparation smoke imported public APIs, inspected the signatures
above, rendered with Agg, and exported a tiny PNG. Do not treat file existence
alone as proof that ranges or labels are visually correct; combine it with
shape/range assertions and, for difficult cases, inspect the figure or pixel
output.
