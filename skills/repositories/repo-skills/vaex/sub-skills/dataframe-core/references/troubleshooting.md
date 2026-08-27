# dataframe-core troubleshooting

## `ModuleNotFoundError: No module named 'vaex'` or missing `vaex-core`

Symptoms:

- `import vaex` fails.
- `vaex.from_arrays` or `vaex.open` is unavailable.
- The installed package only includes an optional subpackage but not core DataFrame APIs.

Actions:

1. Check the active Python environment, not the repository checkout.
2. Install the public Vaex package set appropriate for the task, usually `pip install vaex` or `conda install -c conda-forge vaex`.
3. For core DataFrame-only use, `vaex-core` is the key distribution, but many users install the `vaex` bundle to get registered IO/accessor plugins.
4. Run `python scripts/dataframe_smoke.py --pretty` from this sub-skill to verify imports and core behavior.

Do not paste private environment paths or cache directories into user-facing runtime instructions.

## `vaex.open` cannot open a file or asks for an optional plugin

Core DataFrame guidance should stop at recognizing the route:

- HDF5/Arrow/Parquet/CSV/FITS/VOTable/cloud/file conversion details belong in `../io-conversion/SKILL.md`.
- Missing packages such as HDF5, Arrow, astro, cloud filesystem, or server/remote plugins are IO or serving issues.
- For a tiny core-only repro, replace the file with `vaex.from_arrays(...)` or `vaex.from_dict(...)`.

## `NameError`, parse errors, or wrong results with column names containing spaces/symbols

Cause: Vaex expressions are parsed. Names like `with space`, `A-B`, `#`, `class`, or names colliding with methods/functions can be ambiguous when embedded in raw expression strings or accessed as attributes.

Safer patterns:

```python
# Good
expr = df['with space'].fillmissing('')
expr2 = df['A-B'] * 2 + df['#']
df['derived value'] = expr2
sample = df.evaluate(df['derived value'], i1=0, i2=5, array_type='python')

# Risky for complex expressions
sample = df.evaluate('with space + "suffix"')
```

Debug checklist:

1. Confirm the exact name with `df.get_column_names(hidden=True)`.
2. Use `df['exact name']` to create an `Expression` object.
3. Build derived expressions by combining `Expression` objects, not by interpolating raw strings.
4. Evaluate only a bounded sample: `df.evaluate(expr, i1=0, i2=10, array_type='python')`.
5. If a virtual-column assignment changed the visible name, check `df.get_column_names()` and `df.virtual_columns`.

## Unexpected memory use from `.values`, `to_numpy`, Pandas conversion, or full `evaluate`

Symptoms:

- Process memory jumps.
- Large file-backed DataFrame becomes slow or crashes.
- A Pandas-like recipe uses `.values` or `to_pandas_df()` early.

Rules:

- `df.evaluate(...)`, `expr.values`, `expr.to_numpy()`, `np.array(df)`, `df.to_pandas_df()`, full `to_records()`, and full `to_dict()` materialize data.
- Use virtual columns for derived data: `df['new'] = df.x * 2`.
- Use `head`, slices, `i1`/`i2`, or `evaluate_iterator(chunk_size=...)` for bounded validation.
- Use `count` and analytics aggregations for compact results; route detailed statistics/groupby/binby to `../expressions-analytics/SKILL.md`.

Pandas-to-Vaex rewrite pattern:

```python
# Instead of pdf['ratio'] = pdf['a'] / pdf['b']; pdf[pdf['ratio'] > 1]
df['ratio'] = df['a'] / df['b']
filtered = df[df['ratio'] > 1]
preview = filtered.head(5).to_records()
```

## Filtered vs unfiltered `evaluate`

`df.evaluate(expression)` uses `filtered=True` by default. On a filtered DataFrame, it returns rows that pass the filter. If you pass `filtered=False`, Vaex evaluates over the unfiltered active range.

Debug pattern:

```python
dff = df[df.x > 1]
filtered_values = dff.evaluate('x', array_type='python')
unfiltered_values = dff.evaluate('x', filtered=False, array_type='python')
```

Use `selection=...` separately for selections. A DataFrame filter and a named selection are different masks.

## Selection did not affect a result

Common causes:

- You called `df.select(...)` but then used a method without `selection=True` or `selection='name'`.
- You expected `df.select(...)` to return a filtered DataFrame. It mutates selection state and returns `None`.
- You used a selection name string that differs from the one you created.

Correct patterns:

```python
df.select(df.x > 0)
count_selected = df.count(selection=True)
values_selected = df.evaluate(df.x, selection=True, array_type='python')

df.select(df.y < 5, name='low_y')
count_low_y = df.count(selection='low_y')
```

If you want a filtered DataFrame, use `dff = df[df.x > 0]` or `df.filter(...)`.

## Missing vs NaN behavior surprises

Vaex distinguishes three concepts:

- `missing`/masked/null: data is absent; common for strings, Arrow arrays, nullable integers, and masks.
- `NaN`: floating-point not-a-number; not the same as null.
- `NA`: union of missing and NaN.

Symptoms and fixes:

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `dropmissing` did not remove `np.nan` | `NaN` is not missing | Use `dropnan` or `dropna` for floats. |
| `dropnan` did not remove `None` strings | strings have missing/null, not NaN | Use `dropmissing` or `dropna`. |
| `count` differs from Pandas expectations | Vaex/Pandas default missing semantics differ for some operations | Inspect with `countmissing`, `countnan`, and `countna`. |
| String expression fails after filling | fill value has incompatible type | Use `df['s'].fillmissing('')` for missing strings. |

Bounded debug:

```python
col = df['maybe missing']
summary = {
    'missing': int(col.countmissing()),
    'na': int(col.countna()),
}
```

For numeric float columns, add `countnan()` as well.

## Virtual-column assignment mistakes

Symptoms:

- Assigning `df['new'] = array` raises a length mismatch on a filtered DataFrame.
- A virtual column does not appear under the expected name.
- A derived column unexpectedly materializes memory.

Actions:

1. If the right-hand side is an expression, assignment creates a lazy virtual column: `df['new'] = df.x * 2`.
2. If the right-hand side is an array, it is an in-memory column and must match the unfiltered DataFrame length.
3. On filtered data, prefer virtual expressions based on existing columns rather than arrays computed from the filtered rows.
4. Confirm with `df.get_column_names(virtual=True)` and inspect `df.virtual_columns` for expression-backed columns.
5. For non-identifier virtual names, always access with brackets: `df['new value']`.

## Concatenation schema surprises

`vaex.concat([df1, df2])` defaults to flexible schema resolution: missing columns are filled with missing values. If that is not acceptable, use `resolver='strict'`.

Before concatenating large inputs:

```python
for i, frame in enumerate(frames):
    print(i, frame.get_column_names(virtual=True), frame.shape)
combined = vaex.concat(frames, resolver='strict')
```

If virtual columns with the same name have different expressions across inputs, validate or rename them first; Vaex may materialize or raise when reconciling schemas.
