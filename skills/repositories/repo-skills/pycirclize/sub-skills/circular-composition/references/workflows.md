# Circular composition workflows

These recipes target pyCirclize 1.10.1 and static Matplotlib output. They use
only in-memory data and public APIs. Keep output paths under the caller's
chosen writable directory; do not fetch example datasets as part of a smoke
run.

## 1. Build and inspect a general Circos layout

```python
from pycirclize import Circos

circos = Circos(
    {"A": 10, "B": (100, 130), "C": 8},
    start=15,
    end=345,
    space=[3, 8, 3],
    sector2clockwise={"C": False},
)

for sector in circos.sectors:
    print(sector.name, sector.start, sector.end, sector.deg_lim, sector.clockwise)

sector_b = circos.get_sector("B")
group_min, group_max = circos.get_group_sectors_deg_lim(["A", "B"])
```

Use the printed values to confirm that caller data coordinates were not
mistaken for global degrees. A tuple range controls the sector's x-coordinate
system and proportional angular width; it does not force that sector to span
the same number of degrees as its numeric value.

For group bands, draw after the lookup:

```python
circos.rect((92, 100), deg_lim=(group_min, group_max), fc="#cccccc", alpha=0.4)
circos.text("A+B", r=105, deg=(group_min + group_max) / 2, adjust_rotation=True)
```

## 2. Choose spaces deliberately

For three sectors and a final gap, a list must contain three values:

```python
Circos({"A": 10, "B": 10, "C": 10}, space=[2, 7, 3], endspace=True)
```

For three sectors with no final gap, provide two values:

```python
Circos({"A": 10, "B": 10, "C": 10}, space=[2, 7], endspace=False)
```

A scalar is the simplest uniform configuration. When groups need larger
between-group gaps, calculate the complete list with the shared utility
`pycirclize.utils.calc_group_spaces`, then inspect the resulting sector
`deg_lim` values. Do not silently truncate or pad a list: a length mismatch is
an input error and should be repaired at construction time.

## 3. Add composition-level primitives

Composition calls can be queued before a Figure exists:

```python
circos.axis(fc="none", ec="black", lw=0.5)
circos.text("Overview", r=50, deg=180, size=12)
circos.line(r=80, deg_lim=(20, 320), color="grey", ls="dashed")
circos.rect((85, 90), deg_lim=(0, 180), fc="tomato", alpha=0.25)
circos.link(("A", 2, 8), ("B", 120, 110), direction=1, color="steelblue")
circos.link_line(("B", 115), ("C", 4), direction=2, color="black")
circos.colorbar(vmin=0, vmax=100, cmap="viridis", label="score")
```

Global primitives accept global degree arguments; `link` and `link_line` accept
sector-local x coordinates. If a link crosses anti-clockwise sectors, keep the
input endpoints in the declared coordinate systems and test direction after
rendering. `allow_twist=False` can resolve a twisted ribbon by reversing the
second endpoint orientation.

## 4. Render into a caller-owned PolarAxes

Use a caller-owned polar axis when composing multiple subplots or when the
caller needs to control the Figure:

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig = plt.figure(figsize=(8, 4), dpi=100)
polar_ax = fig.add_subplot(121, projection="polar")
other_ax = fig.add_subplot(122)

fig2 = circos.plotfig(ax=polar_ax)
assert fig2 is fig
# Add other_ax content here if needed.
fig.savefig("combined.png", bbox_inches="tight")
```

`plotfig(ax=...)` requires a polar axes object. Passing a normal subplot raises
`ValueError`; create it with `projection="polar"` rather than trying to reuse a
Cartesian axis.

## 5. Add and retain legends

The composition and its axes do not exist until rendering. Add a legend after
`plotfig()` and save the returned Figure:

```python
from matplotlib.lines import Line2D

fig = circos.plotfig()
handles = [Line2D([], [], color="tomato", label="category A")]
circos.ax.legend(handles=handles, loc="upper right")
fig.savefig("with-legend.png", dpi=120, bbox_inches="tight")
```

For multiple legends, save the first return value from `circos.ax.legend()`,
re-add it with `circos.ax.add_artist()`, and then create the next legend. This
is ordinary Matplotlib legend lifecycle management; pyCirclize does not
provide a separate global legend registry.

Do not use `circos.savefig()` for this lifecycle. It calls `plotfig()` and
saves immediately, and its documented static-export path does not preserve a
legend or other edits added afterward. If no post-render edits are required,
`circos.savefig("static.png")` is sufficient.

## 6. Use a colorbar with normalized data

The colorbar is queued at the Circos level and is created during `plotfig()`:

```python
circos.colorbar(
    bounds=(0.82, 0.25, 0.03, 0.5),
    vmin=-1,
    vmax=1,
    cmap="coolwarm",
    orientation="vertical",
    label="effect",
    tick_kws={"labelsize": 8},
)
fig = circos.plotfig()
fig.savefig("with-colorbar.png", bbox_inches="tight")
```

Choose bounds relative to the parent axes and leave enough room in the Figure
for tight bounding-box export. The `vmin`/`vmax` pair is a normalization
contract; it does not rescale any track data by itself.

## 7. Static smoke and safe export

Run the bundled script from an installed environment:

```shell
python scripts/circos_smoke.py --output /tmp/pycirclize-circular-smoke.png
```

The script selects the Agg backend before importing pyplot, uses fixed values
rather than random or downloaded data, validates expected `ValueError` cases,
uses a temporary directory for the managed `savefig()` check, and writes only
the explicit output artifact. Treat a pre-existing output as a safety error
rather than overwriting it; choose a new path for a rerun.

## Boundary decisions

- A track, line/scatter/bar/heatmap, annotation, or `add_track` data workflow
  belongs in [`plot-primitives`](../../plot-primitives/SKILL.md).
- Chord/radar table normalization and factory-specific input behavior belongs
  in [`data-parsers`](../../data-parsers/SKILL.md).
- BED/GenBank/GFF/cytoband, biological features, and tree initialization belong
  in [`genomics-and-trees`](../../genomics-and-trees/SKILL.md).
- Optional tooltips are an interactive Jupyter concern. Core composition and
  Agg export remain valid without `ipympl`.
