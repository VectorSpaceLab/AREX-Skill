# Circular composition API reference

This reference distills the public `Circos` and `Sector` composition APIs in
pyCirclize 1.10.1. It is intentionally limited to layout orchestration and
composition-level drawing. Track-local plotting is covered by
[`plot-primitives`](../../plot-primitives/SKILL.md); matrix/radar factories are
covered by [`data-parsers`](../../data-parsers/SKILL.md); biological formats and
trees are covered by [`genomics-and-trees`](../../genomics-and-trees/SKILL.md).

## Coordinate model

- `Circos` uses angular coordinates in degrees for public sector and global
  methods, and radius coordinates in the plotting range 0--100 (with labels or
  legends commonly placed above 100).
- Matplotlib receives radians internally. `plotfig()` places zero at the top
  and uses the clockwise polar direction for the rendered canvas. Do not
  pre-convert public degree inputs to radians.
- A sector declared as `{"A": 10}` has x coordinates `0..10`. A sector declared
  as `{"A": (100, 140)}` has x coordinates `100..140` and size `40`; the tuple
  endpoints are data coordinates, not angular degrees.
- Sector angular width is proportional to sector size after the configured
  spaces are removed. `sector.deg_lim` reports the resulting angular interval;
  `sector.start`/`end` report the sector's x-coordinate interval.

## Constructor and inspection

```python
Circos(
    sectors: Mapping[str, Numeric | tuple[Numeric, Numeric]],
    start: float = 0,
    end: float = 360,
    *,
    space: Numeric | Sequence[Numeric] = 0,
    endspace: bool = True,
    sector2clockwise: dict[str, bool] | None = None,
    show_axis_for_debug: bool = False,
)
```

`sectors` preserves mapping order. Numeric values are converted to ranges
`(0, value)`; tuple/list values must be strictly increasing. `start` and `end`
are the global degree bounds and must satisfy `-360 <= start < end <= 360`; a
full span cannot exceed 360 degrees. A scalar `space` is reused for each gap.
For a sequence, the required length is the number of sectors when
`endspace=True`, otherwise the number of gaps (`len(sectors) - 1`). The final
space is ignored as a gap when `endspace=False`; it is represented internally
as zero. Excessive total space raises `ValueError`.

Useful read-only properties:

- `circos.deg_lim`, `deg_size`, `rad_lim`, `rad_size`: global bounds and spans.
- `circos.sectors`: ordered `Sector` objects.
- `circos.tracks`: flattened list of tracks across sectors.
- `circos.ax`: the polar axes after `plotfig()`; accessing it earlier raises
  `ValueError`.
- `sector.name`, `start`, `end`, `size`, `center`, `deg_lim`, `rad_lim`,
  `clockwise`, and `tracks` expose the layout needed to calculate positions.

Use `circos.get_sector(name)` for a named lookup. Unknown names raise
`ValueError`. `get_group_sectors_deg_lim(names)` returns the minimum and maximum
reported angular degree across the named sectors, which is useful for group
bands or labels. It also fails through `get_sector()` if a name is unknown.

## Composition-level primitives

All of these calls queue content; they do not require an axes object at call
time. Render only after the complete composition is defined.

### `axis(**kwargs)`

Adds a full circular axis using patch properties such as `fc`, `ec`, `lw`,
`ls`, `alpha`, and `hatch`. It is equivalent to two layered global rectangles
so the face is behind and the edge is in front. For a sector/track-local axis,
route to plot-primitives instead.

### `text(text, *, r=0, deg=0, adjust_rotation=False, orientation="horizontal", **kwargs)`

Queues text at a global degree and radius. `adjust_rotation=True` derives a
readable rotation from the degree and `orientation` (`horizontal` or
`vertical`); otherwise pass ordinary Matplotlib text properties such as `size`,
`color`, `ha`, `va`, and `rotation`.

### `line(*, r, deg_lim=None, arc=True, **kwargs)`

Adds a global arc or straight polar line. `r` may be a scalar or `(r0, r1)`;
`deg_lim=None` means the full `circos.deg_lim`. Set `arc=False` for a straight
line between the degree bounds. Patch styling is passed through to Matplotlib.

### `rect(r_lim=(0, 100), deg_lim=None, **kwargs)`

Adds an annular rectangle. `r_lim` is a radius interval and `deg_lim` defaults
to the global degree range. Use `fc`/`color`, `ec`, `lw`, `hatch`, and `alpha`
for styling. For a band covering selected sectors, combine
`get_group_sectors_deg_lim()` with `deg_lim`.

### `link(...)`

```python
circos.link(
    (sector1, start1, end1),
    (sector2, start2, end2),
    r1=None,
    r2=None,
    *,
    color="grey",
    alpha=0.5,
    height_ratio=0.5,
    direction=0,
    arrow_length_ratio=0.05,
    allow_twist=True,
    **kwargs,
)
```

The two regions are `(sector_name, x_start, x_end)`. Their x values are
validated against the corresponding sector ranges, including anti-clockwise
coordinate conversion. `r1` and `r2` default to the lowest radius of the
tracks in each target sector, or 100 if no track exists. `direction` is `0`
(no arrow), `1` (region 1 to region 2), `-1` (region 1 from region 2), or `2`
(bidirectional). `height_ratio` controls the Bezier control height. With
`allow_twist=False`, pyCirclize reverses the second radial orientation when
needed to avoid a twisted link. Pass patch properties like `ec`, `lw`, `ls`,
`hatch`, and `zorder` through `**kwargs`; `color` and `alpha` are applied by the
method.

For directed links across sectors with different directions, first inspect
both sectors' `clockwise` values and retain each endpoint in its own x range.
Use a small synthetic plot and render it; visual direction can be wrong even
when construction succeeds if endpoints were transformed manually.

### `link_line(...)`

```python
circos.link_line(
    (sector1, position1),
    (sector2, position2),
    r1=None,
    r2=None,
    *,
    color="black",
    height_ratio=0.5,
    direction=0,
    arrow_height=3.0,
    arrow_width=2.0,
    **kwargs,
)
```

This joins two single sector positions with a Bezier line. Positions are in
sector x coordinates; radii default as for `link`. Direction values have the
same four meanings. `arrow_height` is in radius units and `arrow_width` in
degree units. Use `link` for interval-to-interval ribbons and `link_line` for
single-position relationships.

### `colorbar(...)`

```python
circos.colorbar(
    bounds=(1.02, 0.3, 0.02, 0.4),
    *,
    vmin=0,
    vmax=1,
    cmap="bwr",
    orientation="vertical",
    label=None,
    colorbar_kws=None,
    label_kws=None,
    tick_kws=None,
)
```

`bounds` is `(x, y, width, height)` in parent-axes inset coordinates. The
method queues creation of a Matplotlib colorbar; it is materialized by
`plotfig()`. `cmap` accepts a Matplotlib colormap name or `Colormap`, and
`orientation` is `vertical` or `horizontal`. Keep the colorbar's `vmin` and
`vmax` aligned with the plotted data's normalization.

## Sector-level composition helpers

`sector.text()` and `sector.rect()` are useful for sector labels and bands, and
`sector.axis()` draws the full sector. `sector.add_track()` creates a track,
but all track-local APIs must be routed to plot-primitives. `sector.x_to_rad(x)`
converts a valid sector x coordinate to an internal radian value; use it for
inspection/debugging rather than pre-converting arguments to public methods.

## Rendering and export lifecycle

### `plotfig`

```python
fig = circos.plotfig(
    dpi=100,
    *,
    ax=None,
    figsize=(8, 8),
    tooltip=False,
)
```

With `ax=None`, pyCirclize creates a new figure and polar axes. With `ax`, the
object must be a Matplotlib `PolarAxes`; a normal Cartesian axis raises
`ValueError`. `plotfig()` initializes polar orientation, materializes queued
patches and callbacks from the Circos/Sector/Track hierarchy, and stores the
axis at `circos.ax`. It returns the owning Figure.

Call it once the composition is ready, then perform Matplotlib edits:

```python
fig = circos.plotfig(ax=polar_ax)
circos.ax.legend(handles=handles, loc="upper right")
fig.savefig("result.png", dpi=120, bbox_inches="tight")
```

A tooltip request (`tooltip=True`) requires an interactive Jupyter-like
runtime and `ipympl`; static Agg export should use the default `False`.

### `savefig`

```python
circos.savefig(
    savefile,
    *,
    dpi=100,
    figsize=(8, 8),
    pad_inches=0.5,
)
```

`savefig()` calls `plotfig()` internally and writes PNG/JPG/SVG/PDF through
Matplotlib with tight bounding-box handling. It does not return the Figure and
normally clears/closes the temporary Figure afterward. Therefore it is the
short path for a static composition, not the path for a custom axis or edits
that must be made after rendering.

The package documentation specifically warns that a user-defined legend,
subtracks, or annotations should be saved through `Figure.savefig()` after
`plotfig()`. A common failure is to add a legend to `circos.ax` after calling
`circos.savefig()`; that saved file is already complete and the temporary
figure has been closed.

## Evidence boundary

Facts above were checked against the installed pyCirclize 1.10.1 public
signatures and behavior, the package README, the Getting Started and Plot Tips
notebooks, the Circos unit tests, and global plotting tests. Notebook examples
were adapted as guidance only; runtime skill files do not depend on a checkout,
notebook, test fixture, or private environment path.
