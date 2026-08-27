# Orange data model and file formats

This reference anchors Orange data-preparation work in `Orange.data`, `Orange.preprocess`, and `Orange.data.pandas_compat`.

## Core model

- `Table` stores rows in `X`, `Y`, `metas`, and `W`.
- `Domain` describes the schema: `attributes`, `class_vars`, `metas`, `class_var`, and `anonymous`.
- `Variable` descriptors define how values are named, parsed, printed, and converted.
- Column lookup can use integer positions, names, or variable objects.
- Direct in-place edits in scripts usually require `with table.unlocked():`.

```python
from Orange.data import Table
iris = Table("iris")
print(iris.domain)
print(iris[0, "petal length"])
```

## Variable kinds

- `ContinuousVariable`: numeric values.
- `DiscreteVariable`: categorical values with an ordered `values` list.
- `StringVariable`: free text and identifiers.
- `TimeVariable`: date/time values, stored internally as UNIX epoch seconds.

Use `Variable.make(...)` when you want Orange to reuse an existing descriptor by name and compatible type.

Derived variables matter in preprocessing: `compute_value` lets Orange carry a transformation into future domain conversions so train and test data receive the same feature construction.

## Construction and conversion

- `Table.from_numpy(domain, X, Y=None, metas=None, W=None, attributes=None, ids=None)` builds a table from arrays.
- `Table.from_domain(domain, n_rows=0, weights=False)` makes an empty or shaped table for a known schema.
- `Table.from_table(domain, source, row_indices=Ellipsis)` and `Table.from_table_rows(source, row_indices)` preserve a source table while re-expressing it in a new domain or row subset.
- `Table.from_file(filename, sheet=None)` loads by extension and optional Excel sheet.
- `Table.save(filename)` dispatches by extension on write.
- `Domain.from_numpy(X, Y=None, metas=None)` creates anonymous domains that can match other anonymous domains by shape and type.

## Reshape and inspection helpers

- `Table.transpose(...)` turns columns into rows; it is the main reshape helper for wide-to-long style changes.
- `Table.shuffle()` randomizes rows for dense tables.
- `Table.is_sparse()` tells you whether save/load or preprocessing may hit sparse-specific limits.
- `Table.get_column(...)` and `Table.set_column(...)` are useful in scripts, but `set_column` expects compatible discrete encodings.
- `Domain.has_discrete_attributes(...)`, `Domain.has_continuous_attributes(...)`, and `Domain.has_time_attributes(...)` are helpful when choosing a preprocess path.
- `Table.checksum()` is useful when you need a cheap stability check after round trips.

## File readers and writers

Orange3 core file workflows support:

- tab-separated values: `.tab`, `.tsv`
- comma-separated values: `.csv`
- Excel: `.xlsx`
- pickle: `.pkl`, `.pickle`
- compressed text/pickle variants: `.gz`, `.bz2`, `.xz` where the reader/writer supports them

`Table.save(...)` chooses a writer from the filename extension. Unknown extensions fail fast.

Text-based data files support two header styles:

1. **Three-line header**
   - line 1: names
   - line 2: types
   - line 3: flags and custom attributes
2. **Single-line header**
   - optional `<flags>#` prefix before each name

Useful tokens:

- types: `discrete` / `d`, `continuous` / `c`, `string` / `s` / `text`, `time` / `t`
- flags: `class` / `c`, `meta` / `m`, `weight` / `w`, `ignore` / `i`

Type annotations can be added to `.tab` and `.csv` exports when a writer supports them. Some text round trips also preserve table attributes in a `.metadata` sidecar.

## Pandas bridge

Use pandas interoperability when a task is easier as a frame reshape before coming back to Orange:

- `Orange.data.pandas_compat.table_from_frame`
- `Orange.data.pandas_compat.table_to_frame`
- `Table.X_df`, `Table.Y_df`, `Table.metas_df`

Example:

```python
from Orange.data.pandas_compat import table_from_frame, table_to_frame
frame = table_to_frame(Table("iris"))
round_trip = table_from_frame(frame)
```

## Practical defaults

- Prefer `Table.from_file(...)` for raw file loads and `Table.save(...)` for exports.
- Prefer `Table.from_table(...)` or `.transform(...)` when you need to move data across domains.
- Use explicit header annotations or `OWEditDomain` when type inference guesses the wrong variable kind.
- Use pickle when you need the safest round trip for sparse tables.

## Provenance note

This reference is distilled from Orange3's public data API documentation, source, and tests. See the repo-level provenance file for the relative evidence-path list and refresh baseline.
