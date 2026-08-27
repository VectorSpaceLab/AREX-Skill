# Data-parser troubleshooting

Use the symptom first, then inspect the parser object before changing plotting
parameters. These cases are derived from the parser/factory source, focused
parser tests, chord/radar notebooks, and installed signatures for pyCirclize
1.10.1.

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ModuleNotFoundError: pycirclize`, pandas, or matplotlib | Base package or runtime dependency is not installed in the active Python | Install pyCirclize with Python >=3.10 and its base dependencies; verify with `python -c "import pycirclize; print(pycirclize.__version__)"`. |
| Tooltip warning about Jupyter/ipympl | `tooltip=True` or tooltip enabling was requested without an interactive IPython session or `ipympl` | Keep core plotting/export on ordinary Matplotlib; install the optional `tooltip` extra and use a Jupyter widget backend only when interactive tooltips are required. |
| `FileNotFoundError` when passing a parser path | The caller supplied a missing path or a path relative to a different working directory | Resolve/check the path in caller code. The bundled smoke helper uses only its own temporary fixtures and is not a data downloader. |
| One giant label or one-column matrix | Wrong `delimiter`, or the file's first column was not intended to be the index | Inspect `dataframe.shape`, `row_names`, and `col_names`; pass `delimiter=","` for CSV and keep the row-label column first. |
| `IndexError` or malformed from-to conversion | A from-to row has fewer than three columns, or `header=False`/`True` does not match the file | Ensure columns 1-3 are from, to, numeric value; choose `header=False` for a truly headerless path. DataFrame column names are not used for positional parsing. |
| `TypeError` during `value <= 0`, `float(value)`, `sum`, or range comparison | Matrix/table cell is a string, missing value, or mixed nonnumeric object | Inspect the offending cells and apply explicit numeric validation/coercion in caller preparation. Do not silently replace missing or malformed values with zero. |
| `ValueError` stating an order is invalid or does not match `all_labels` | `order` is not `asc`, `desc`, or an explicit list containing exactly all generated labels | Print `matrix.all_names`; use the exact label set and desired order. Remember sorting is by accumulated node size, not alphabetic order. |
| Unexpected sector total or missing/merged label | Duplicate row/column labels or overlap between row and column namespaces | Normalize labels before `Matrix`; inspect `to_sectors()` and `to_links()`. Use unique canonical names when row and column roles must stay separate. |
| A duplicate from-to pair gives a surprising size/link | The parser overwrites the stored value for the later identical directed pair but accumulates both rows into endpoint totals | Aggregate duplicates upstream or reject them. If intentional, compare `to_fromto_table()` with `to_sectors()` before plotting. |
| A reverse relationship is missing | From-to conversion is directed; it does not mirror `A -> B` into `B -> A` | Add the reverse row explicitly or perform a documented undirected aggregation before conversion. |
| `ValueError: vmax must be larger than vmin` | `Circos.radar_chart` received `vmin >= vmax` | Choose a strict `vmin < vmax` range that contains all series values. Test this before constructing the chart. |
| `grid_interval_ratio` is invalid | A truthy value is outside `(0, 1]` | Use `None` (or `0`, which is falsy) to omit grid lines, or a positive ratio no larger than 1. |
| Radar construction fails with `value=... is not in valid range` | One or more table cells lie outside `vmin..vmax` (or are nonnumeric) | Report min/max and offending labels, then widen the range or normalize the data. Do not merely change `r_lim`, which controls radius rather than value scale. |
| Radar colors or handler lookup raises `KeyError` | A custom `cmap` dict does not contain every row name, or a handler assumes labels not present | Use exact `RadarTable.row_names` keys; return style kwargs for every handler call. A string cmap avoids missing-key mappings. |
| Radar tooltip text is absent | Markers were not requested, or the environment is noninteractive | Set `marker_size > 0` to attach tooltip strings. PNG export remains valid without the optional `ipympl` extra; interactive display is a separate optional path. |
| Chord chart has no expected links | Cells are zero/negative, labels were merged, or from-to rows were filtered | Inspect `matrix.to_links()` and `matrix.to_fromto_table()` before calling the factory. Only positive values become links. |
| Chord `cmap`/`link_cmap` styling is incomplete | The mapping omits a name or the directed pair spelling does not match | Use exact labels and pair keys `(from_label, to_label, color)`. Unmapped chord names fall back to gray; handler output can override link kwargs. |
| `Bed.records` is shorter than the file | Comments, nonempty short rows, or invalid integer coordinates are silently skipped; an empty line can instead raise while the first field is accessed | Remove empty lines, validate input row count independently, and inspect each skipped line. Use one interval per chromosome for `initialize_from_bed`; repeated chromosomes overwrite earlier sector ranges there. |
| A BED cytoband is white unexpectedly | The fifth field does not match a key in `cytoband_cmap` | Inspect `str(record.score)` and add that exact class key. Unmapped classes intentionally fall back to white. |
| PNG export fails or no file appears | Plotting was not completed, the output parent does not exist, or the path is not writable | Start with `circos.plotfig()`/`circos.savefig()` on a writable local path; create caller-owned output directories explicitly. Run the bundled validator for a temporary, isolated export check. |

There is no pyCirclize CLI to debug. Missing GPU/accelerator support is not a
parser issue: core parser and Matplotlib workflows are CPU/any-backend paths.
For low-level coordinate/range errors route to [plot-primitives](../../plot-primitives/SKILL.md);
for GenBank/GFF, biological feature, or tree errors route to
[genomics-and-trees](../../genomics-and-trees/SKILL.md).
