# Data formats and validation

Use this reference before converting a user file. pyCirclize parsers are small
adapters around pandas or a tab-delimited reader; they preserve many input
assumptions instead of imposing a schema-normalization layer.

## Matrix files and DataFrames

### Accepted shape

`Matrix` accepts a path-like value or a `pandas.DataFrame`.

- Path inputs are read with the supplied `delimiter` and `index_col=0`. The
  first file column is therefore row labels, not numeric data.
- DataFrame inputs are consumed as-is. Keep numeric values in the cells and
  put stable labels in the index and columns. A rectangular DataFrame is valid;
  the common chord example is a square DataFrame with the same labels on both
  axes.
- Public names are stringified, but the underlying DataFrame is not generally
  coerced or cleaned. Duplicate index/column labels, mixed types, missing
  values, and nonnumeric cells can produce ambiguous sectors or fail later in
  comparisons/arithmetic.

Minimal square input:

```python
import pandas as pd
from pycirclize import Circos

matrix_df = pd.DataFrame(
    [[2, 1], [3, 0]], index=["A", "B"], columns=["A", "B"]
)
fig = Circos.chord_diagram(matrix_df, cmap={"A": "steelblue", "B": "tomato"}).plotfig()
```

For CSV, use `Matrix(path, delimiter=",")`. If a TSV is accidentally read
with a comma delimiter, pandas will usually expose a one-column DataFrame with
compound labels; inspect `matrix.dataframe.shape`, `row_names`, and
`col_names` before plotting.

### Matrix conversion semantics

For every positive cell, `to_links()` emits a pair of sector regions. Zero and
negative cells are omitted. `to_sectors()` sums the positive contribution seen
at row/column endpoints. This is a directed representation: `A -> B` and
`B -> A` are separate links and contribute separately. A diagonal cell creates
a self-link with two regions in the same sector.

`to_fromto_table()` is a positive-cell audit view with exactly `from`, `to`, and
`value` columns. It is not a lossless representation of nonpositive cells.
When labels overlap between row and column axes, the implementation's dict
aggregation can merge names; use one canonical label namespace and check the
returned mapping if that matters.

## From-to tables

The conversion accepts either a path or DataFrame:

```python
from pycirclize.parser import Matrix

fromto = pd.DataFrame(
    [["A", "B", 10], ["A", "C", 5], ["B", "A", 3]],
    columns=["from", "to", "value"],  # names are informational
)
matrix = Matrix.parse_fromto_table(fromto, order="desc")
```

The parser reads **columns 1, 2, and 3 by position**, so names such as
`source`, `target`, and `weight` are fine. The value must support comparison to
zero and conversion to float; for DataFrame input, keep the third column
numeric rather than numeric-looking strings because the retained value is used
again when the Matrix is built. Negative values are skipped. A path with a
header uses `header=True` (default); use `header=False` for a headerless file.
The file delimiter applies to this parser too.

Labels are collected from retained rows. The default order is first-seen order.
`asc` and `desc` sort by accumulated endpoint size, not alphabetically. An
explicit list must match the complete label set exactly, including no extras or
omissions. The conversion fills every pair in the resulting square DataFrame
with zero when no directed pair was present.

Duplicate directed pairs are a difficult input: the later row replaces the
stored cell value while both rows affect the accumulated size used for sorting.
Aggregate duplicates upstream (or reject them) when totals must be consistent.
Asymmetric input is supported and should remain asymmetric; do not mirror a
from-to table unless the application explicitly asks for undirected weights.

## General tables

`Table`, `StackedBarTable`, and `RadarTable` share the same path/DataFrame
contract: path inputs use `delimiter`/`sep` and `index_col=0`; DataFrames keep
their existing index and columns. Row and column names are exposed as strings.

- A table for stacked bars should contain numeric values. `stacked_bar_heights`
  is column-major (one list per table column), while bottoms accumulate within
  each row across columns.
- `row_sum_vmax` is the maximum row total and is useful as the sector size for
  a horizontal stacked bar. `calc_bar_label_x_list(track_size)` returns evenly
  spaced row centers. `calc_barh_label_r_list` and `calc_barh_r_lim_list`
  return descending radial row positions/limits.
- A radar table uses rows as series/targets and columns as axes. The values for
  one row are returned in column order. Column labels become the radar labels;
  row labels become line/marker labels and tooltip prefixes.
- Table color helpers return label-to-color dictionaries. For a custom radar
  palette, pass a dict whose keys exactly cover the table's row names. For
  custom column label styles, use `label_kws_handler` at the radar factory.

Nonnumeric cells can remain unnoticed in a bare `Table` but will fail when
stack/radar arithmetic or plotting tries to compare/sum them. Normalize with
`pd.to_numeric(..., errors="raise")` in caller-owned preparation code so the
failing column/row is clear; do not silently coerce scientific input to zero.

## BED records

BED input is local, tab-delimited text. Each usable line has:

```text
chromosome<TAB>start<TAB>end[<TAB>name<TAB>score]
```

Comment lines beginning with `#`, nonempty rows shorter than three fields,
and rows whose first three fields cannot be parsed as chromosome + integer
start/end are skipped. Extra fields after score are ignored. Empty lines should
be removed before parsing: the implementation accesses the first CSV field
before its short-row check. `BedRecord.size` is `end-start`. This permissive
behavior is useful for a smoke check but means a typo can reduce record count
without raising; compare the parsed count with an expected count when data
completeness matters.

`Circos.initialize_from_bed` converts records into `{chromosome: (start, end)}`
sectors, so repeated chromosome rows overwrite earlier ranges in that factory.
For a chromosome-size BED, use one interval per chromosome. `add_cytoband_tracks`
reads a BED-shaped cytoband file and uses the fifth-field `score` text as a
cytoband class; missing classes fall back to white. For GenBank/GFF and other
feature semantics, route to [genomics-and-trees](../../genomics-and-trees/SKILL.md).
