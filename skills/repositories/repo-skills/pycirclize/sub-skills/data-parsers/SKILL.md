---
name: data-parsers
description: "Routes pyCirclize matrix, table, BED, stacked-bar, radar, from-to,
  chord, and radar-chart data preparation workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Data parsers

Use this route when the task is to turn tabular data into pyCirclize sectors,
links, stacked bars, or radar series, or to build a chord/radar chart from a
file, `pandas.DataFrame`, or parser object.

## Route by input and output

- **Chord or graph-like data:** read [API reference](references/api-reference.md)
and [data formats](references/data-formats.md). Use `Matrix` for a matrix and
`Matrix.parse_fromto_table` for three-column from-to data, then call
`Circos.chord_diagram`. Use `to_sectors()` for `Circos(...)` and `to_links()`
for explicit `circos.link` workflows.
- **Radar data:** use `RadarTable` or let `Circos.radar_chart` wrap a path,
DataFrame, or table. Confirm numeric values and `vmin < vmax` before plotting;
use the radar workflow for colors, labels, tooltips, and export.
- **Stacked bars and labels:** use `StackedBarTable` for row/column names,
heights, bottoms, row totals, and label positions. Hand drawing and track
coordinate details belong to [plot-primitives](../plot-primitives/SKILL.md).
- **BED/cytoband preparation:** use `Bed` for local tab-delimited BED records
and route genomic feature semantics, GenBank/GFF, and trees to
[genomics-and-trees](../genomics-and-trees/SKILL.md).

Read the linked references before choosing a parser. They contain the verified
signatures, positional column assumptions, conversion semantics, and recovery
steps that are intentionally not duplicated here. Run the bundled deterministic
check when a small parser-plus-export smoke test is useful:

```bash
python scripts/validate_matrix_and_radar.py
```

The helper creates only temporary local fixtures and PNGs; it makes no network
requests and does not modify the checkout or a user-specified data file.

## Fast checks before plotting

1. Decide whether the source is a square/rectangular matrix, a three-column
   from-to table, a row-indexed table, or BED records; do not infer a schema
   from a filename alone.
2. Preserve labels in the DataFrame index/columns. File inputs use the first
   column as the index, and parser names are exposed as strings.
3. Pass the actual delimiter for CSV or other delimited files. A wrong
   delimiter often creates one malformed label column rather than a useful
   parser error.
4. Check numeric cells before `Matrix`, `StackedBarTable`, or `RadarTable`
   plotting. Parser constructors are intentionally lightweight and do not
   normalize arbitrary DataFrames for you.
5. For radar, choose `vmin` and `vmax` so every plotted value is in range and
   ensure `vmin < vmax`; invalid range errors may be raised while the factory
   builds the series.

Do not use this route for low-level `Track`/`Sector` drawing, annotations, or
coordinate debugging; use `plot-primitives`. Do not use it for GenBank/GFF
feature extraction or Newick/tree styling; use `genomics-and-trees`.
