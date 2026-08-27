# Parser and chart API reference

Read this file when selecting a parser, checking a signature, or handing data
to a high-level chart factory. The signatures below were inspected from the
installed pyCirclize **1.10.1** package and cross-checked against the parser
source and focused parser/plot tests.

## Public imports and runtime boundary

```python
from pycirclize import Circos
from pycirclize.parser import Bed, Matrix, RadarTable, StackedBarTable
from pycirclize.parser.table import Table
```

`pycirclize.parser` exports `Bed`, `Genbank`, `Gff`, `Matrix`, `RadarTable`,
and `StackedBarTable`; the reusable `Table` base class is defined in
`pycirclize.parser.table` and should be imported from that module.

The package requires Python >=3.10 and uses `biopython`, `matplotlib`, `numpy`,
and `pandas`. `ipympl` is only the optional `tooltip` extra. These parsers and
factories use ordinary CPU Matplotlib rendering; there is no CLI or
accelerator-specific backend.

## `Matrix`

```text
Matrix(matrix: str | Path | pd.DataFrame, *, delimiter: str = "\\t")
Matrix.parse_fromto_table(
    fromto_table: str | Path | pd.DataFrame, *,
    order: str | list[str] | None = None,
    delimiter: str = "\\t", header: bool = True,
) -> Matrix
matrix.sort(order: str | list[str] = "asc") -> Matrix
matrix.to_sectors() -> dict[str, float]
matrix.to_links() -> list[tuple[tuple[str, float, float], tuple[str, float, float]]]
matrix.to_fromto_table() -> pd.DataFrame
```

- A path is read with `pandas.read_csv(..., delimiter=delimiter, index_col=0)`;
  a DataFrame is used directly. The matrix may be rectangular. `row_names`,
  `col_names`, `all_names`, and `dataframe` expose the retained labels/data.
- `to_sectors()` returns the name-to-total mapping used by `Circos`. `to_links()`
  returns two `(name, start, end)` regions per positive cell, in the order
  consumed by `circos.link(*link)`. Zero and negative cells do not produce
  links. Positive diagonal cells become self-links with the parser's two
  non-overlapping regions.
- `to_fromto_table()` emits a DataFrame with columns `from`, `to`, `value` for
  positive cells only. It is useful for inspecting or reordering a matrix.
- `parse_fromto_table()` reads the first three **columns by position** as
  from-label, to-label, and value; DataFrame column names are not required.
  `header=True` means the first line of a path is a header; use `header=False`
  for a headerless file. Nonnegative values are retained. The conversion
  creates a square matrix over every label seen in a retained row.
- `order=None` preserves first-seen label order from the conversion. `order="asc"`
  or `"desc"` sorts by the accumulated node size. A list must contain exactly
  the set of generated labels, otherwise a `ValueError` is raised. Other order
  values also raise `ValueError`.
- Duplicate from-to keys are not aggregated by the implementation: the later
  value replaces the earlier value in the generated cell, while the size
  accumulator sees both rows. Treat duplicate directed pairs as an input error
  unless that asymmetry is intentional and you have checked the resulting
  sectors.

## `Table`, `StackedBarTable`, and `RadarTable`

```text
Table(table_data: str | Path | pd.DataFrame, *, delimiter: str = "\\t")
StackedBarTable(table_data: str | Path | pd.DataFrame, *, delimiter: str = "\\t")
RadarTable(table_data: str | Path | pd.DataFrame, *, delimiter: str = "\\t")
```

`Table` is the shared base adapter; `StackedBarTable` and `RadarTable` extend
it with plotting-oriented transformations. Import the base class from
`pycirclize.parser.table`, not from `pycirclize.parser`.

A path is loaded with `pandas.read_csv(..., sep=delimiter, index_col=0)`.
`Table` exposes `dataframe`, stringified `row_names`/`col_names`, `row_num`,
`col_num`, and deterministic color dictionaries from
`get_row_name2color(cmap="tab10")` / `get_col_name2color(cmap="tab10")`.
Color cycling is global to the helper, so use a known colormap and consume the
returned mapping rather than relying on a previous global cycle state.

`StackedBarTable` adds:

- `row_sum_vmax`: largest sum of a row;
- `row_name2sum`: row label to sum;
- `stacked_bar_heights`: one list per column, each ordered by row;
- `stacked_bar_bottoms`: cumulative bottom lists in column order;
- `calc_bar_label_x_list(track_size)`: centered x positions for vertical bars;
- `calc_barh_label_r_list(track_r_lim)`: descending row centers for horizontal
  bars;
- `calc_barh_r_lim_list(track_r_lim, width=0.8)`: per-row radial limits;
  `width` must be in the plotting range expected by the track helper.

Use these values with `Track.stacked_bar` or `Track.stacked_barh`; the actual
track API and coordinate conventions belong to [plot-primitives](../../plot-primitives/SKILL.md).

`RadarTable` adds `row_name2values`, a row-label to value-list mapping in column
order, and `get_row_tooltip(target_row)`, which returns one string per column in
the form `row-label\\ncolumn-label:value`.

## `Bed`

```text
Bed(bed_file: str | Path)
Bed.records -> list[BedRecord]
BedRecord(chr, start, end, name=None, score=None)
BedRecord.size -> int
```

`Bed` reads a local tab-delimited file. Blank/malformed rows, comment rows, and
rows with fewer than three fields are skipped. The first three fields are
chromosome, integer start, and integer end; fields four and five become
`name` and `score` when present. `size` is `end - start`. Coordinates are
consumed as zero-based BED coordinates by `Circos.initialize_from_bed`; for
cytobands, the `score` text is used to select a color. Genomic format semantics
beyond BED are owned by [genomics-and-trees](../../genomics-and-trees/SKILL.md).

## High-level chord factory

```text
Circos.chord_diagram(
    matrix: str | Path | pd.DataFrame | Matrix, *,
    start=0, end=360, space=0, endspace=True, r_lim=(97, 100),
    cmap="viridis", link_cmap=None, ticks_interval=None, order=None,
    label_kws=None, ticks_kws=None, link_kws=None,
    link_kws_handler=None,
) -> Circos
```

A path/DataFrame is wrapped in `Matrix`; an existing `Matrix` is reused. If
`order` is set, the factory calls `matrix.sort(order)`. It initializes sectors
from `to_sectors()`, creates an outer track per sector, and sends every
`to_links()` result to `circos.link`. A string `cmap` cycles colors for names; a
mapping supplies name colors (unmapped names fall back to gray). `link_cmap` is
an explicit list of `(from_label, to_label, color)` overrides. `link_kws_handler`
receives `(from_label, to_label)` and can return per-link keyword overrides.

Use `circos.plotfig()` to obtain a Matplotlib Figure for legends/custom axes,
or `circos.savefig(path)` for a simple PNG/JPEG/SVG/PDF export. The factory
does not validate application-specific label uniqueness or business semantics;
validate the Matrix before plotting.

## High-level radar factory

```text
Circos.radar_chart(
    table: str | Path | pd.DataFrame | RadarTable, *,
    r_lim=(0, 100), vmin=0, vmax=100, fill=True, marker_size=0,
    bg_color="#eeeeee80", circular=False, cmap="Set2",
    show_grid_label=True, grid_interval_ratio=0.2,
    grid_line_kws=None, grid_label_kws=None, grid_label_formatter=None,
    label_kws_handler=None, line_kws_handler=None,
    marker_kws_handler=None,
) -> Circos
```

A path/DataFrame is wrapped in `RadarTable`; the factory creates one sector with
size equal to the number of columns, one track at `r_lim`, and one closed series
per row. A string `cmap` cycles row colors; a dict maps row labels to colors.
Handlers receive a column name for labels or a row name for lines/markers.
`marker_size > 0` adds markers and attaches `RadarTable.get_row_tooltip` text
to them. `fill=False`, `bg_color=None`, or `grid_interval_ratio=None` are useful
for sparse/custom plots.

The factory requires `vmin < vmax` and raises `ValueError` otherwise. A
nonzero `grid_interval_ratio` must be in `(0, 1]`; `None` or `0` skips grid
construction because the implementation guards this option by truthiness.
Series values are checked against the selected range by the track plotting
methods, so out-of-range or nonnumeric values should be fixed before calling
the factory. The table must have at least one column for a meaningful radar
chart.
