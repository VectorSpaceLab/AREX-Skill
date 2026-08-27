# dataframe-core API reference

Signatures below were verified against the installed Vaex 4.19.0 package set used during skill construction. Prefer public `vaex` and `DataFrame` APIs; do not depend on repository checkout internals.

## Constructors and top-level helpers

| API | Signature | Use | Notes |
| --- | --- | --- | --- |
| `vaex.open` | `vaex.open(path, convert=False, progress=None, shuffle=False, fs_options={}, fs=None, *args, **kwargs)` | Open a DataFrame from a path, glob/list, remote Vaex URL, or registered file opener. | Core can mention this for entry; route file-format/export/conversion/plugin/cloud details to `../io-conversion/SKILL.md`. `convert` can create optimized files and needs disk-space planning. |
| `vaex.from_arrays` | `vaex.from_arrays(**arrays)` | Create an in-memory `DataFrameLocal` from named arrays/lists. | Best for tiny tests and already-in-memory data. All arrays must match length. |
| `vaex.from_dict` | `vaex.from_dict(data)` | Create an in-memory DataFrame from `{column_name: values}`. | Keeps dynamic or non-identifier column names. Values are passed to `from_arrays`. |
| `vaex.from_pandas` | `vaex.from_pandas(df, name='pandas', copy_index=False, index_name='index')` | Convert a Pandas DataFrame. | Converts an already eager Pandas object; use `copy_index=True` only if the index should become a Vaex column. |
| `vaex.from_csv` | `vaex.from_csv(filename_or_buffer, copy_index=False, chunk_size=None, convert=False, fs_options={}, progress=None, fs=None, **kwargs)` | Read a CSV into Vaex, optionally chunking/converting. | Mention for basics only. Detailed parsing, conversion, and file IO are owned by `../io-conversion/SKILL.md`. |
| `vaex.from_arrow_table` | `vaex.from_arrow_table(table)` | Wrap a PyArrow `Table`. | Useful for strings, nulls, list/struct values, and Arrow interoperability. |
| `vaex.from_dataset` | `vaex.from_dataset(dataset)` | Wrap a Vaex dataset object in a DataFrame. | Use when a registered opener or lower-level Vaex dataset is already available. |
| `vaex.concat` | `vaex.concat(dfs, resolver='flexible')` | Row-concatenate DataFrames. | `flexible` fills missing columns with missing values; `strict` requires matching schemas. |
| `vaex.example` | `vaex.example()` | Load Vaex's bundled/example astronomical simulation dataset. | Good for demos, but it may require example-data availability. Prefer `from_arrays` for deterministic smoke tests. |

## DataFrame inspection and validation

| API | Signature | Use | Lazy/materialization note |
| --- | --- | --- | --- |
| `df.get_column_names` | `df.get_column_names(virtual=True, strings=True, hidden=False, regex=None, dtype=None)` | List visible real and virtual columns, with filters. | Metadata-only; safe first inspection. Hidden names start with `__` unless `hidden=True`. |
| `df.shape` | property returning `(len(df), len(df.get_column_names()))` | Quick dimensions. | On filtered DataFrames, row count can require evaluating/counting the filter mask. |
| `len(df)` | `len(df)` | Number of rows after filter. | Same filtered caveat as `shape[0]`. |
| `df.head` | `df.head(n=10)` | Return a shallow DataFrame slice with first rows. | Safe for preview; convert only the small slice if needed. |
| `df.count` | `df.count(expression=None, binby=[], limits=None, shape=128, selection=False, delay=False, edges=False, progress=None, array_type=None)` | Count rows or non-missing values; can apply selection. | Scalar/count result is compact. Rich binned/statistical uses route to `../expressions-analytics/SKILL.md`. |
| `df.copy` | `DataFrameLocal.copy(column_names=None, treeshake=False)` | Shallow copy, optionally subset columns. | Cheap; does not copy underlying arrays/file data. Tracks virtual-column dependencies. |

## Access, slicing, filtering, and selection

| API | Use | Notes |
| --- | --- | --- |
| `df['name']` | Get an `Expression` for a column or expression string. | Safest for names with spaces, punctuation, keywords, symbols, or attribute collisions. |
| `df.name` | Attribute shorthand for identifier-like columns. | Avoid for non-identifiers and names that collide with methods/functions. |
| `df[['x', 'y']]` | Shallow column subset DataFrame. | Dependencies for virtual expressions are tracked. |
| `df[:100]`, `df[-10:]` | Shallow row slice. | Does not materialize all columns. |
| `df[df.x > 0]` | Return a filtered shallow DataFrame. | Equivalent filter semantics narrow by default. |
| `df.filter(expression, mode='and')` | Return a filtered shallow copy; mode can combine with existing filter. | `mode='or'` can broaden an existing filter, unlike Pandas-style chained filtering. |
| `df.select(boolean_expression, mode='replace', name='default')` | Store a named selection on the DataFrame. | Apply later with `selection=True`, `selection='name'`, or selection-aware methods. |
| `df.select_non_missing(drop_nan=True, drop_masked=True, column_names=None, mode='replace', name='default')` | Select rows with non-missing/non-NaN values across columns. | Does not drop rows; creates a selection mask. |
| `df.dropmissing`, `df.dropnan`, `df.dropna` | Return shallow filtered DataFrames. | `dropmissing` handles absent/null/masked; `dropnan` handles float NaN; `dropna` handles both. |

## Evaluation and materialization boundaries

| API | Signature / pattern | Use | Warning |
| --- | --- | --- | --- |
| `df.evaluate` | `df.evaluate(expression, i1=None, i2=None, out=None, selection=None, filtered=True, array_type=None, parallel=True, chunk_size=None, progress=None)` | Evaluate one expression or a list for all or part of the DataFrame. | This returns arrays and may need the result to fit in memory. Prefer bounded `i1`/`i2`, `selection`, or compact aggregations. |
| `df.evaluate_iterator` | `df.evaluate_iterator(expression, s1=None, s2=None, out=None, selection=None, filtered=True, array_type=None, parallel=True, chunk_size=None, prefetch=True, progress=None)` | Stream expression values in chunks. | Use for validation or controlled export-like work when full materialization is too large. |
| `Expression.evaluate` | `expr.evaluate(i1=None, i2=None, out=None, selection=None, parallel=True, array_type=None)` | Evaluate an expression object. | Same materialization warning as `df.evaluate`. |
| `Expression.values` / `.to_numpy()` / `np.array(df)` | Eager conversion. | Use only for intentionally small data or final handoff where memory is known safe. |
| `df.to_records`, `df.to_dict`, `df.to_arrays`, `df.to_items` | Convert to Python/list/array structures, optionally chunked. | Use only for previews or controlled chunks; full calls materialize selected columns. |

`array_type` options commonly include `None`, `'numpy'`, `'arrow'`, `'python'`, and `'list'` depending on the method. Arrow-backed string columns may remain Arrow arrays when `array_type=None`.

## Virtual columns and derived data

| API | Signature / pattern | Use | Notes |
| --- | --- | --- | --- |
| `df['new'] = expr` | `DataFrame.__setitem__(name, value)` | Add a real column if `value` is a supported array, otherwise add a virtual column/expression. | For derived data, pass an expression to stay lazy. Arrays must match the unfiltered DataFrame length. |
| `df.add_virtual_column` | `df.add_virtual_column(name, expression, unique=False)` | Add named lazy expression. | If `name` is not a valid Python identifier, Vaex may store a valid internal name; use `get_column_names` and bracket access to confirm. |
| `df.virtual_columns` | mapping of virtual column name to expression string | Debug what is virtual. | Treat as inspection aid; prefer public add/delete methods for mutations. |
| `df.delete_virtual_column(name)` | delete a virtual column when available | Remove a virtual column. | Validate with `get_column_names()` afterward. |

## Missing-value helpers

| Helper | Meaning |
| --- | --- |
| `expr.ismissing()`, `expr.countmissing()`, `expr.fillmissing(value)` | Null/masked/missing values; valid for non-float types such as strings and Arrow nulls. |
| `expr.isnan()`, `expr.countnan()`, `expr.fillnan(value)` | Floating-point NaN values. |
| `expr.isna()`, `expr.countna()`, `expr.fillna(value)` | Union of missing and NaN. |
| `df.dropmissing`, `df.dropnan`, `df.dropna` | Return shallow filtered DataFrames that remove rows matching the corresponding condition. |
| `df.select_non_missing` | Create a selection rather than filtering or dropping. |

## Non-identifier column name rules

Vaex supports columns such as `'with space'`, `'A-B'`, `'#'`, `'class'`, `'data'`, and Unicode names. Use these safe patterns:

```python
col = df['with space']
df['ratio value'] = df['A-B'] / df['#']
small = df.evaluate(df['ratio value'], i1=0, i2=5, array_type='python')
```

Avoid constructing raw strings such as `'with space + 1'` unless you have validated how Vaex parsed the name. Build expressions from `Expression` objects instead.
