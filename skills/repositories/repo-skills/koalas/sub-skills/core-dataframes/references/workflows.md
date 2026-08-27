# Core DataFrames workflows

Use these workflows to translate pandas-style snippets to Koalas while preserving distributed execution and avoiding accidental driver collection.

## 1. Create tiny fixtures and migrated objects

```python
import pandas as pd
import databricks.koalas as ks

pdf = pd.DataFrame(
    {
        "id": [1, 2, 3],
        "city": ["London", "New York", "Helsinki"],
        "temp": [20.0, 21.0, None],
    },
    index=pd.Index([10, 11, 12], name="row_id"),
)

kdf = ks.from_pandas(pdf)
assert list(kdf.columns) == ["id", "city", "temp"]
assert kdf.index.name == "row_id"
```

Validation steps:

1. Confirm `kdf.dtypes` against expected pandas dtypes.
2. Use `kdf.head(n)` for bounded display.
3. Use `kdf.to_pandas()` only for tiny fixtures or after a bounded filter/sample.

For a generated range fixture:

```python
kdf = ks.range(0, 5)  # one int64 column: id
kdf["squared"] = kdf["id"] * kdf["id"]
```

## 2. Convert between pandas, Koalas, and Spark without losing index intent

Pandas to Koalas:

```python
kdf = ks.from_pandas(pdf)
```

Koalas to pandas, only after bounding:

```python
small_pdf = kdf[kdf["id"] <= 3].to_pandas()
```

Koalas to Spark while preserving the index as a column:

```python
sdf = kdf.to_spark(index_col="row_id")
# Spark operations happen here.
kdf_again = sdf.to_koalas(index_col="row_id")
```

Avoiding default-index overhead when starting from Spark:

```python
# Prefer this when an existing Spark column identifies rows.
kdf = sdf.to_koalas(index_col="id")

# This attaches a default index and can be expensive for large data.
kdf_with_default = sdf.to_koalas()
```

Route deeper Spark schema, SQL, storage, reader, and writer tasks to `spark-io-sql`.

## 3. Migrate a pandas snippet with unsafe column names

Problematic pandas snippet:

```python
pdf = pd.DataFrame([[1, 2, 3]], columns=["a", "A", "__column__"])
pdf["a"] + pdf["A"]
```

Koalas-safe migration:

```python
rename = {"a": "a_lower", "A": "a_upper", "__column__": "column_value"}
kdf = ks.from_pandas(pdf.rename(columns=rename))
kdf["total"] = kdf["a_lower"] + kdf["a_upper"]
```

Why: Spark SQL can treat case-only names as ambiguous unless configured for case sensitivity, and Koalas reserves leading/trailing double-underscore names for internal columns. Normalize columns before conversion or immediately after reading data.

Validation steps:

```python
assert len(set(map(str.lower, kdf.columns))) == len(kdf.columns)
assert not any(str(c).startswith("__") and str(c).endswith("__") for c in kdf.columns)
```

## 4. Select, index, and update safely

Label selection:

```python
subset = kdf.loc[kdf["id"] >= 2, ["city", "temp"]]
```

Position selection:

```python
first_two_cols = kdf.iloc[:, :2]
first_row_temp = kdf.iloc[0, 2]
```

Scalar access:

```python
value_by_label = kdf.at[10, "city"]
value_by_pos = kdf.iat[0, 1]
```

Column creation and assignment:

```python
kdf["temp_f"] = kdf["temp"] * 9 / 5 + 32
kdf = kdf.assign(temp_missing=kdf["temp"].isna())
```

Avoid creating columns by assigning a new attribute, for example `kdf.new_col = ...`; use bracket assignment or `assign`.

## 5. Clean missing data

```python
clean = kdf.dropna(subset=["temp"])
filled = kdf.fillna({"temp": 0.0, "city": "unknown"})
forward = kdf.fillna(method="ffill")
backward = kdf.fillna(method="bfill")
mask = kdf["temp"].notna()
```

Validation steps:

```python
assert filled["temp"].isna().sum() == 0
assert clean["temp"].notna().all()
```

If pandas code uses column-axis `fillna(axis=1)`, DataFrame-valued fills, or unsupported `limit` combinations, rewrite to per-column expressions or collect only bounded data.

## 6. Convert and inspect dtypes

```python
kdf["id32"] = kdf["id"].astype("int32")
kdf["temp_float"] = kdf["temp"].astype("float64")
print(kdf.dtypes)
```

Normalize mixed-type object columns before construction:

```python
pdf["id"] = pd.to_numeric(pdf["id"], errors="coerce")
kdf = ks.from_pandas(pdf)
```

Check Spark-facing types when needed:

```python
spark_dtype = kdf["temp_float"].spark.data_type
```

For detailed Spark schema and IO behavior, route to `spark-io-sql`.

## 7. Use string APIs without local iteration

```python
cities = kdf["city"].str.strip().str.lower()
flags = kdf["city"].str.contains("new", case=False, regex=False)
lengths = kdf["city"].str.len()
parts = kdf["city"].str.split(" ", expand=True)
dummies = kdf["city"].str.get_dummies(sep="|")
```

Prefer vectorized `Series.str` methods over Python loops. If pandas code has:

```python
[x.lower() for x in pdf["city"]]
```

translate it to:

```python
kdf["city"].str.lower()
```

## 8. Use datetime APIs

```python
kdf["event_ts"] = ks.to_datetime(kdf["event_ts"], format="%Y-%m-%d")
kdf["event_year"] = kdf["event_ts"].dt.year
kdf["event_month"] = kdf["event_ts"].dt.month
kdf["event_date"] = kdf["event_ts"].dt.strftime("%Y-%m-%d")
idx = ks.date_range(start="2021-01-01", periods=3, freq="D", name="day")
```

Validation steps:

```python
assert str(kdf["event_ts"].dtype).startswith("datetime64")
assert idx.name == "day"
```

Timezone-aware pandas dtypes and pandas `Timedelta` need special validation; prefer simple timestamp/date columns unless the environment has explicit support.

## 9. Use categorical-like APIs cautiously

```python
pser = pd.Series(pd.Categorical(["small", "large", "small"]))
kser = ks.from_pandas(pser)
print(kser.cat.categories)
print(kser.cat.codes.head(3))
```

Guidance:

- Read `Series.cat.categories`, `Series.cat.ordered`, and `Series.cat.codes` when available.
- Avoid relying on pandas category mutators unless validated in the runtime; several category dtypes and metadata mutations have limited support.
- For one-hot features, prefer `ks.get_dummies(kdf, columns=[...])` or `Series.str.get_dummies` for delimiter-separated strings.

## 10. Reshape and combine

Concatenate rows:

```python
combined = ks.concat([kdf1, kdf2], axis=0, ignore_index=False)
```

Merge on columns:

```python
joined = left.merge(right, how="left", on="id", suffixes=("_left", "_right"))
# Equivalent top-level form:
joined = ks.merge(left, right, how="left", on="id")
```

Melt wide to long:

```python
long = ks.melt(kdf, id_vars=["id"], value_vars=["temp", "humidity"], var_name="metric")
```

One-hot encode:

```python
encoded = ks.get_dummies(kdf, columns=["city"], prefix="city")
```

Validation steps:

```python
assert "id" in joined.columns
assert set(["id", "metric", "value"]).issubset(set(long.columns))
```

## 11. Compute basic statistics

```python
summary = kdf[["id", "temp"]].describe()
counts = kdf.count()
means = kdf[["id", "temp"]].mean()
missing = kdf.isna().sum()
unique_cities = kdf["city"].nunique()
quantiles = kdf["temp"].quantile([0.25, 0.5, 0.75])
```

Remember that actions such as `count`, `describe`, `to_pandas`, and some scalar reductions trigger Spark jobs.

## 12. Replace local iteration with Koalas APIs

Pandas/local pattern:

```python
result = []
for x in pdf["temp"]:
    result.append(x * x if x is not None else None)
```

Koalas vectorized replacement:

```python
squared = kdf["temp"] * kdf["temp"]
```

If complex custom functions are required, route to `apply-groupby-window` for type-hint-aware `apply`/`transform`/batch APIs.

## 13. Validate a migration with a tiny expected pandas sample

```python
expected = pdf.rename(columns={"temp": "temperature"}).head(3)
actual = kdf.rename(columns={"temp": "temperature"}).head(3).to_pandas()
pd.testing.assert_frame_equal(actual, expected)
```

Keep this pattern limited to tiny deterministic fixtures. For large data, validate invariants (`count`, min/max ranges, schema/dtypes, sample rows) without collecting the full result.
