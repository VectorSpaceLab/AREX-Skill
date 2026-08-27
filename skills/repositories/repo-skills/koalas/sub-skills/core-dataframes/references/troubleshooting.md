# Core DataFrames troubleshooting

## Unsupported or missing pandas APIs

Symptoms:

- `NotImplementedError: The method pd.Series... is not implemented`
- `AttributeError` for a pandas method or property that exists locally
- pandas code expects an in-memory array, xarray object, pickle, memory report, or iterator

Actions:

1. Look for a Koalas vectorized equivalent first: arithmetic/comparison operators, `Series.str`, `Series.dt`, missing-data methods, reductions, `ks.to_datetime`, `ks.get_dummies`, `DataFrame.merge`, and `ks.concat`.
2. If the unsupported operation is local-only and data is known tiny, explicitly bound then collect:
   ```python
   pdf = kdf.head(1000).to_pandas()
   ```
3. If the operation is a custom elementwise or grouped function, route to `apply-groupby-window` for type-hint-aware `apply`, `transform`, `groupby`, rolling, or expanding guidance.
4. If the operation is storage, SQL, Spark schema, or file IO, route to `spark-io-sql`.

Do not silently replace an unsupported pandas API with `to_pandas()` on unbounded data.

## Duplicated columns

Symptoms:

- Spark error containing `Reference 'a' is ambiguous`
- Selection returns the wrong column or fails after `concat`, `merge`, `get_dummies`, or manual column assignment
- A pandas snippet intentionally uses duplicate column labels

Cause: Spark SQL generally cannot resolve duplicate column names, and Koalas inherits that constraint.

Fix before converting to Koalas:

```python
pdf = pdf.copy()
pdf.columns = [f"{name}_{i}" if list(pdf.columns).count(name) > 1 else name for i, name in enumerate(pdf.columns)]
kdf = ks.from_pandas(pdf)
```

Better, assign semantic names:

```python
pdf = pdf.rename(columns={"a": "a_left"})
```

Validation:

```python
assert len(kdf.columns) == len(set(kdf.columns))
```

## Case-sensitive or case-only duplicate columns

Symptoms:

- Columns `a` and `A` work in pandas but are ambiguous in Koalas/Spark
- `kdf["a"]` fails or points to an unexpected Spark field

Default action: rename to distinct lower/upper-safe names before Koalas conversion.

```python
pdf = pdf.rename(columns={"a": "a_lower", "A": "a_upper"})
kdf = ks.from_pandas(pdf)
```

Advanced action: Spark can be configured for case-sensitive SQL before Koalas creates/uses a Spark session, but this is a global Spark behavior and belongs in environment/configuration planning, not a default migration. Prefer renaming for portable skills.

Validation:

```python
lowered = [str(c).lower() for c in kdf.columns]
assert len(lowered) == len(set(lowered))
```

## Reserved `__column__`-style names

Symptoms:

- Failures involving internal columns such as `__index_level_0__`, `__natural_order__`, or a generated temporary name
- A user column begins and ends with double underscores, for example `__column__`
- Spark conversion unexpectedly drops, overwrites, or conflicts with an internal field

Cause: Koalas uses leading/trailing double-underscore column names internally for index, natural order, group keys, temporary values, and similar bookkeeping.

Fix:

```python
safe_columns = {
    c: str(c).strip("_") or "column"
    for c in pdf.columns
    if str(c).startswith("__") and str(c).endswith("__")
}
pdf = pdf.rename(columns=safe_columns)
kdf = ks.from_pandas(pdf)
```

Validation:

```python
assert not any(str(c).startswith("__") and str(c).endswith("__") for c in kdf.columns)
```

## Collecting to pandas or NumPy accidentally

Symptoms:

- Driver out-of-memory errors
- Very slow `to_pandas()`, `to_numpy()`, `values`, list conversion, or pandas-only validation
- Code compares a full Koalas result with a full pandas result on large data

Actions:

1. Bound first: `head`, `sample`, filters, or small fixture construction.
2. Validate distributed invariants instead of collecting everything:
   ```python
   assert kdf.count().to_pandas()["id"] > 0
   assert kdf["id"].min() >= 0
   ```
3. For debugging, collect only relevant columns and rows:
   ```python
   debug_pdf = kdf.loc[kdf["id"] < 10, ["id", "status"]].to_pandas()
   ```
4. For Spark-side validation and plans, route to `spark-io-sql`.

## Non-iterability of Series and Index

Symptoms:

- `TypeError` or `NotImplementedError` when using `for x in kser`, `list(kser)`, `sum(kser)`, `min(kser)`, `max(kser)`, or list comprehensions
- External Python library expects a local iterable

Cause: Koalas `Series` and `Index` are distributed and intentionally do not expose local iteration.

Rewrite local iteration to vectorized APIs:

```python
# Instead of: [x * x for x in kdf["x"]]
kdf["x_squared"] = kdf["x"] * kdf["x"]

# Instead of: max(kdf["x"])
max_x = kdf["x"].max()
```

If a third-party function truly requires local data, collect only bounded data:

```python
values = kdf["x"].head(100).to_pandas().tolist()
```

## Default index performance

Symptoms:

- Spark-to-Koalas conversion is unexpectedly slow
- Plans show index-generation columns or single-partition work
- Repeated conversions lose the original pandas/Spark row identity

Cause: Spark DataFrames have no pandas-style index. If Koalas cannot use an existing index column, it attaches a default index. The default sequential index is convenient but can be expensive on large data.

Actions:

1. Preserve index when going Koalas to Spark:
   ```python
   sdf = kdf.to_spark(index_col="row_id")
   ```
2. Reuse an existing Spark column when returning to Koalas:
   ```python
   kdf = sdf.to_koalas(index_col="row_id")
   ```
3. If no stable index exists and data is large, route option tuning for `compute.default_index_type` to `configuration-extensions`.
4. For IO/storage conversion details, route to `spark-io-sql`.

## Dtype conversion and mixed-type gotchas

Symptoms:

- Arrow or Spark type-inference errors during `ks.from_pandas` or `ks.DataFrame(...)`
- `TypeError` for mixed integers/strings in one column
- Unexpected Spark decimal, date, timestamp, string/object, or nullable behavior

Actions:

1. Normalize pandas columns before conversion:
   ```python
   pdf["amount"] = pd.to_numeric(pdf["amount"], errors="coerce")
   pdf["event_ts"] = pd.to_datetime(pdf["event_ts"], errors="coerce")
   kdf = ks.from_pandas(pdf)
   ```
2. Use `astype` for explicit Koalas dtypes:
   ```python
   kdf["amount"] = kdf["amount"].astype("float64")
   kdf["id"] = kdf["id"].astype("int64")
   ```
3. Validate both Koalas and Spark-facing types when Spark interop matters:
   ```python
   print(kdf.dtypes)
   print(kdf["amount"].spark.data_type)
   ```
4. Avoid relying on unsupported pandas-specific dtypes without a runtime check: timedeltas, categorical dtype metadata, sparse dtype, timezone-aware pandas dtypes, unsigned integer extension dtypes, pandas nullable boolean/string dtypes, and mixed-type object columns.

## String accessor gotchas

Symptoms:

- Regex behavior differs from a pandas snippet
- `Series.str.split(..., expand=True)` changes the shape
- Null strings produce surprising boolean/null results

Actions:

1. Set `regex=False` for literal substring checks:
   ```python
   kdf["city"].str.contains(".", regex=False)
   ```
2. Specify `na=` when boolean masks must not contain nulls:
   ```python
   mask = kdf["city"].str.contains("new", case=False, regex=False, na=False)
   ```
3. Validate expanded string operations on a small sample before applying to production data.

## Datetime gotchas

Symptoms:

- Parsing differs from pandas
- Timezone-aware values fail or lose timezone detail
- `date_range` or `dt` fields behave differently from pandas edge cases

Actions:

1. Prefer explicit parse formats:
   ```python
   kdf["ts"] = ks.to_datetime(kdf["ts"], format="%Y-%m-%d", errors="coerce")
   ```
2. Keep timestamps timezone-naive unless the environment is explicitly validated for timezone handling.
3. Use `Series.dt` fields for extraction instead of collecting to pandas.
4. Validate with a tiny sample covering nulls, leap days, month boundaries, and formatting requirements.

## Categorical gotchas

Symptoms:

- `pd.Categorical` conversion fails during Arrow inference
- `Series.cat` has categories/codes but mutating category metadata is incomplete
- One-hot encoded column names collide

Actions:

1. For category-like values, consider keeping strings and using `ks.get_dummies`:
   ```python
   encoded = ks.get_dummies(kdf, columns=["category"], prefix="category")
   ```
2. When using `Series.cat`, validate available fields:
   ```python
   print(kser.cat.categories)
   print(kser.cat.codes.head(5))
   ```
3. Rename categories or prefixes to prevent duplicate dummy column names.
4. Avoid pandas category mutator-heavy workflows unless a small runtime probe proves support.

## Index and MultiIndex surprises

Symptoms:

- Operations do not check duplicated index values like pandas would
- MultiIndex columns become stringified in Spark conversion
- `reset_index` or `set_index` changes column names unexpectedly

Actions:

1. Check index uniqueness before logic that requires it:
   ```python
   assert kdf.index.is_unique
   ```
2. When converting to Spark, choose explicit `index_col` names:
   ```python
   sdf = kdf.to_spark(index_col="row_id")
   ```
3. For MultiIndex columns, validate `to_spark(index_col=...)` output column names on a tiny sample before relying on downstream Spark SQL.

## Quick diagnostic checklist

- Can the task be done with Koalas vectorized APIs without collecting?
- Are column names unique, case-safe, and free of leading/trailing double underscores?
- Is the index explicit when converting to/from Spark?
- Are dtypes normalized before `ks.from_pandas` or Spark conversion?
- Is any `to_pandas()` / `to_numpy()` call bounded and justified?
- Should this task route to Spark IO/SQL, apply/groupby/window, or configuration/extensions instead of core DataFrames?
