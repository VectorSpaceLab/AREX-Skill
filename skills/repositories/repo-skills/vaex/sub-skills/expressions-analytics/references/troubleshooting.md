# Vaex expressions and analytics troubleshooting

Use this matrix when a Vaex analytic workflow fails or gives surprising results. Route non-analytics issues as follows: DataFrame construction basics to `../dataframe-core/SKILL.md`, file import/export to `../io-conversion/SKILL.md`, plots/widgets to `../visualization-jupyter/SKILL.md`, and ML pipelines to `../ml-pipelines/SKILL.md`.

## Quick triage commands

Run these against the user's DataFrame (or a safe copy) before large jobs:

```python
print(df.shape)
print(df.get_column_names())
print(df.data_type('candidate_column'))
print(df.evaluate(candidate_expr, i1=0, i2=min(5, len(df))))
```

For this sub-skill's installed-package smoke check:

```bash
python scripts/analytics_smoke.py --help
python scripts/analytics_smoke.py
```

## Failure matrix

| Symptom | Likely cause | Diagnosis | Fix |
| --- | --- | --- | --- |
| `SyntaxError` when evaluating a column with spaces, punctuation, or digits at the start | Expression string was parsed as Python-like syntax | Check `df.get_column_names()` and test `df['actual column']` | Use bracket access: `df['column with spaces']`; pass expression objects to stats and `vaex.agg`, e.g. `vaex.agg.sum(df['long name'])`. |
| `NameError` or `KeyError: Unknown variables or column` | Misspelled column, missing virtual column, or expression namespace collision | Print names; run `df.validate_expression(expr)` if available; evaluate a small slice | Correct spelling, use `df['name']`, or create the virtual column before using it. Avoid local Python variables inside expression strings unless registered as Vaex variables/functions. |
| Boolean expression uses Python `and`/`or` and fails or behaves oddly | Vaex expressions need vectorized operators | Inspect expression string | Use `&`, `|`, and `~` with parentheses: `(df.x > 0) & (df.y < 1)`. In string expressions, use Vaex-compatible boolean syntax and validate on a slice. |
| `.values`, `.to_numpy()`, `np.array(df)`, or `to_pandas_df()` exhausts memory | Eager materialization of a full expression/DataFrame | Search code for eager APIs; compare `len(df)` to memory budget | Replace with virtual columns, `df.evaluate(..., i1=..., i2=...)`, `evaluate_iterator`, statistics, groupby/binby, or export/materialize via `../io-conversion/SKILL.md` when persistence is required. |
| Virtual column is slow in repeated heavy stats | It is recomputed lazily for each pass | Time a tiny representative stat; inspect virtual dependency depth | Combine delayed stats in one execution, simplify the expression, or persist/materialize the derived column through IO workflows if memory/disk budget allows. |
| `df.count()` differs from `df.count('col')` | `df.count()` counts rows; `df.count('col')` counts non-missing/non-NaN values for that expression | Check `df.col.isna().sum()` or `df.col.value_counts(dropna=False)` | Choose the count that matches intent; use `dropna`, `dropnan`, and `dropmissing` flags for unique/value_counts/nunique. |
| Groupby includes a `None`, masked, or NaN group | Vaex keeps missing groups by default | `summary.key.tolist()` or `df.key.value_counts(dropna=False)` | Filter/drop missing keys first if undesired, or document the missing group. For counts use `value_counts(dropna=True)` to drop both NaN and missing values. Fixed-set helpers such as `vaex.groupby.GrouperLimited` can be version-sensitive around missing values in some published wheel combinations; if that path raises a constructor `TypeError`, simplify the grouping or treat it as a version-specific repo/runtime issue. |
| Sorted groupby puts missing values last | Vaex sorting places missing/nan/NA at the end regardless of direction in several sorted outputs | Run `groupby(..., sort=True, ascending=...)` on a small sample | Treat missing as a separate bucket; fill or filter before sorting if a custom missing order is required. |
| `RowLimitException` during groupby | Too many unique groups/combinations relative to `row_limit` | Lower dimensions, run `value_counts` on individual keys, or use a small `row_limit` intentionally | Increase `row_limit` only after estimating result size; group fewer keys; categorize/bin high-cardinality keys; use `binby` numeric grids where appropriate. |
| Dense multi-key groupby is unexpectedly huge | `assume_sparse=False` or dense categorical combinations create many rows | Check key cardinalities and `assume_sparse` setting | Use `assume_sparse='auto'` or `True`; set `row_limit`; aggregate only needed keys. |
| `binby` result has wrong shape or error about limits | `shape` or `limits` does not match `binby` dimensions | Compare `len(binby)`, `limits`, and `shape` | Use `shape=64` and `limits=[lo, hi]` for 1D; `shape=(nx, ny)` and `limits=[[xlo, xhi], [ylo, yhi]]` for 2D. Validate with `shape=4` first. |
| Binned counts do not sum to row count | Rows outside `limits` are excluded; NaN/missing keys may not be inside regular bins | Compare with `df.count()` and use wider limits or edge bins where supported | Use explicit limits, `limits='minmax'`, percentage limits, or `edges=True` for supported count aggregations. |
| Approximate percentile differs from exact small-sample result | `percentile_approx` is grid/histogram based | Run exact NumPy on a tiny slice and compare; inspect `percentile_shape` and `percentile_limits` | Increase `percentile_shape`, tighten limits, or state approximation tolerance. |
| Mutual information looks unstable | MI is estimated on a grid controlled by `mi_shape`/`mi_limits` | Vary `mi_shape` on a small sample or subset | Choose stable limits, increase `mi_shape` within budget, and document that MI is approximate. |
| `value_counts` result is too large | High-cardinality column | Use `unique(..., limit=...)`, groupby `row_limit`, or sampled diagnostics | Do not print/store full high-cardinality counts unless requested and affordable. |
| String accessor fails or differs from Pandas | Operation unsupported for Arrow strings/nulls, regex flag mismatch, or null strings | Evaluate `df.string_col.str.<op>(...).evaluate(i1=0, i2=...)` on null-containing sample | Use supported `expr.str` operations, set `regex=False` for literal matching, fill/drop missing strings where appropriate, or use `str_pandas` only when the result is known to fit and Pandas behavior is required. |
| Null strings counted unexpectedly | Missing and NaN are distinct concepts in Vaex | Compare `value_counts(dropna=False)`, `dropmissing=True`, and `dropnan=True` | Use the specific drop flags required by the analysis; do not assume Pandas defaults. |
| Datetime accessor raises a Pandas dtype/resolution error | Some datetime units (for example day resolution) are not accepted by Pandas-backed accessors | Check `df.data_type('time_col')`; reproduce on first rows | Cast first: `df['time_ns'] = df.time_col.astype('datetime64[ns]')`, then use `df.time_ns.dt.month`/etc. |
| Datetime comparisons with strings behave unexpectedly | Mixed string/datetime types | Check data type and evaluate a small boolean expression | Convert strings to datetime virtual columns with `.astype('datetime64[ns]')`; compare against `np.datetime64(...)`. |
| Struct field access fails | Field name/index wrong or expression is not a struct | Check `df.data_type('struct_col')` and evaluate `df.struct_col.tolist(i1=0, i2=1)` only for tiny data | Use `df.struct_col.struct.get('field')` or `df.struct_col[:, 'field']`; project fields before groupby. |
| Geo transformation/accessor missing | Optional package/import or wrong accessor surface | Check `hasattr(df, 'geo')` and method names with `dir(df.geo)` | Use DataFrame-level `df.geo` methods for coordinate virtual columns; route astro IO/plugin installation issues to `../io-conversion/SKILL.md`. |
| Join raises `column name collision` | Same non-key column names on left and right without prefixes/suffixes | Inspect `set(left.get_column_names()) & set(right.get_column_names())` | Pass `rprefix`, `rsuffix`, `lprefix`, or `lsuffix`, e.g. `left.join(right, on='id', rsuffix='_right')`. |
| Join raises duplication error | Right-side join key has duplicate values and row multiplication is disabled | Run `right.key.value_counts(dropna=False)` or a grouped count | Deduplicate/aggregate the right table first, or pass `allow_duplication=True` only if row multiplication is intended and output size is acceptable. |
| Joined result ignores a filter | Vaex joins the full underlying DataFrame because filters may change | Check whether either side is filtered; compare `len(df)` and intended extracted length | Use `filtered.extract()` before joining when the current filtered subset is the intended join input. |
| Left join keeps unmatched rows with missing right columns | Expected left join semantics | Count non-missing right columns after join | Use `how='inner'` for only matched rows; remember full/outer joins are not supported. |
| Join on NaN/null keys gives missing right values | NaN/null keys do not match ordinary right keys unless matching null semantics apply to the specific dtype/path | Create a tiny key sample and join it | Fill or normalize join keys before joining if missing keys should match a sentinel category. |
| Sorting puts missing values at the end | Vaex sort pushes missing/nan/NA values to the end regardless of `ascending` | Sort a tiny sample | Fill missing values or create a separate sort key if custom missing order matters. |

## Safe recovery playbooks

### Expression parse/name error

1. Print available columns: `df.get_column_names()`.
2. Replace fragile strings with expression objects: `expr = df['exact name'] * 2`.
3. Evaluate at most five rows: `df.evaluate(expr, i1=0, i2=5)`.
4. Add a virtual column only after validation: `df['new'] = expr`.
5. Use the virtual column in statistics/groupby.

### Missing categories in groupby

1. Inspect counts with `df.key.value_counts(dropna=False)`.
2. Decide whether missing values are a real category or should be excluded.
3. If excluded, filter first: `dff = df[~df.key.isna()]` or equivalent expression.
4. If included, use `sort=True` for deterministic output and document the missing bucket.
5. Add `row_limit` when key cardinality is uncertain.

### Large join with duplicate keys

1. Never convert the right table to Pandas or NumPy for diagnosis.
2. Use Vaex counts on the right key: `right.key.value_counts(dropna=False)`; if too large, use `unique(..., limit=...)` or a guarded groupby.
3. If duplicates are accidental, aggregate/deduplicate the right side to one row per key.
4. If duplicates are expected, estimate row multiplication and only then use `allow_duplication=True`.
5. Use prefixes/suffixes and validate a small joined preview.

### Facet/binby shape mismatch

1. Write down the intended dimensions (`x`, `y`, optional `z`, selections/statistics).
2. Make `limits` and `shape` explicit for each `binby` expression.
3. Run a tiny grid first (`shape=4` or `(4, 4)`).
4. Check `grid.shape` before handing the result to plotting or downstream code.
5. Route visualization-specific facet layout/heatmap issues to `../visualization-jupyter/SKILL.md`.
