# Parser-to-plot workflows

These recipes are deliberately small and use only public APIs. They assume
pyCirclize 1.10.1, pandas, and a Matplotlib backend. For headless execution,
select `Agg` before importing pyplot or pyCirclize.

## 1. Matrix to chord diagram

1. Load a DataFrame or file with the correct delimiter and first-column index.
2. Inspect `Matrix.row_names`, `col_names`, `dataframe.shape`, and
   `to_sectors()`; decide whether overlapping row/column labels are intended.
3. Optionally call `matrix.sort("asc")`, `matrix.sort("desc")`, or
   `matrix.sort([...])`. An explicit list must cover every generated label.
4. Call `Circos.chord_diagram(matrix_or_input, ...)`. Use `cmap` for sector/link
   defaults, `link_cmap` for exact directed-pair colors, and
   `link_kws_handler(from_label, to_label)` for conditional link properties.
5. Use `plotfig()` for legends or a caller-owned Matplotlib axis; use `savefig()`
   for a simple file export and verify that the file exists and is non-empty.

```python
import pandas as pd
from pycirclize import Circos
from pycirclize.parser import Matrix

fromto_df = pd.DataFrame(
    [["A", "B", 2], ["A", "C", 1], ["B", "A", 3]],
    columns=["from", "to", "value"],
)
matrix = Matrix.parse_fromto_table(fromto_df, order="desc")
circos = Circos.chord_diagram(
    matrix,
    space=3,
    cmap={"A": "#4477AA", "B": "#CC6677", "C": "#117733"},
    link_cmap=[("A", "B", "black")],
    link_kws=dict(ec="black", lw=0.5),
)
circos.savefig("chord.png")
```

For a non-tabular matrix file, construct `Matrix(path, delimiter=",")` (or
another delimiter) and pass the resulting object to the factory; the
`chord_diagram` signature has no separate delimiter parameter.

For explicit low-level composition, use `Circos(matrix.to_sectors())` and call
`circos.link(*link)` for each item in `matrix.to_links()`. This belongs to the
parser-to-composition boundary; detailed link styling and sector drawing are in
[plot-primitives](../../plot-primitives/SKILL.md) and the root composition route.

### Asymmetric or self-link data

Keep directed rows as supplied. `A -> B` and `B -> A` produce distinct links;
`A -> A` is a self-link. Before plotting, compare the expected directed pair
set with `{(link[0][0], link[1][0]) for link in matrix.to_links()}`. If a
workflow needs an undirected graph, aggregate/mirror it explicitly before
calling the parser and document that transformation.

## 2. Radar table to PNG

1. Prepare a DataFrame with target/series names in the index and numeric metric
   names in the columns.
2. Select `vmin`/`vmax` that contain every value. The factory rejects
   `vmin >= vmax` and track methods reject values outside the range.
3. Use a string colormap or a row-name-to-color dict. Set `marker_size > 0` to
   attach per-point tooltips; tooltips are useful in interactive notebooks but
   core PNG export does not require `ipympl`.
4. Use `grid_interval_ratio=None` to omit grid lines, or a value in `(0, 1]`.
   Set `fill=False` and `bg_color=None` for an unfilled custom style.
5. Call `plotfig()` before adding a legend through `circos.ax`; call `savefig()`
   for the simple export path.

```python
import pandas as pd
from pycirclize import Circos

scores = pd.DataFrame(
    [[0.8, 0.6, 0.9], [0.4, 0.9, 0.5]],
    index=["model-a", "model-b"],
    columns=["precision", "recall", "robustness"],
)
circos = Circos.radar_chart(
    scores,
    vmin=0,
    vmax=1,
    marker_size=3,
    cmap={"model-a": "#4477AA", "model-b": "#CC6677"},
    grid_label_formatter=lambda value: f"{value:.1f}",
)
fig = circos.plotfig()
circos.ax.legend(loc="upper right")
fig.savefig("radar.png", dpi=100, bbox_inches="tight")
```

`RadarTable(scores).get_row_tooltip("model-a")` exposes the same text attached
to markers when markers are enabled. For a TSV, pass the path directly (the
parser default is tab) or construct `RadarTable(path, delimiter="\t")`. For a
CSV or another delimiter, construct `RadarTable(path, delimiter=",")` and pass
that object to `Circos.radar_chart`; the factory's `table` argument has no
separate delimiter parameter.

## 3. Stacked-bar preparation

Use `StackedBarTable` when several plotting calls need consistent row totals,
heights, bottoms, and labels:

```python
from pycirclize.parser import StackedBarTable

sb = StackedBarTable(table_df)
sector_size = sb.row_sum_vmax
heights = sb.stacked_bar_heights
bottoms = sb.stacked_bar_bottoms
x_labels = sb.calc_bar_label_x_list(track_size=sector_size)
```

Pass the original `sb.dataframe` to `Track.stacked_bar` or
`Track.stacked_barh`; pass `heights`/`bottoms` only when composing an equivalent
custom plot. Horizontal bars use `calc_barh_label_r_list(track.r_plot_lim)` and
`calc_barh_r_lim_list(track.r_plot_lim, width=...)`. Coordinate and style details
are routed to [plot-primitives](../../plot-primitives/SKILL.md).

## 4. Local BED preparation

Use `Bed(path).records` to inspect chromosome, integer start/end, optional name
and score, and record sizes. For a chromosome-size file with one row per
chromosome:

```python
from pycirclize import Circos

circos = Circos.initialize_from_bed("chromosomes.bed", space=2)
```

For UCSC-like cytobands, call `circos.add_cytoband_tracks((95, 100), path)` and
provide `cytoband_cmap` when the score classes need custom colors. This route
only prepares BED-shaped coordinates. Route GenBank/GFF parsing and feature
selection to [genomics-and-trees](../../genomics-and-trees/SKILL.md).

## 5. Deterministic smoke validation

Run the bundled helper from this directory or any current working directory:

```bash
python scripts/validate_matrix_and_radar.py
```

It exercises DataFrame and delimiter-aware local-file inputs, from-to
conversion, table/radar helpers, a tiny BED parse, chord and radar PNG export,
and the documented invalid radar range. It uses a temporary directory and
returns nonzero on an assertion failure.
