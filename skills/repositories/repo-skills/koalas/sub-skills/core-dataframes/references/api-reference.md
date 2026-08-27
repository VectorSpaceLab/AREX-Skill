# Core DataFrames API reference

This reference is for agents operating on Koalas 1.x (`databricks.koalas`) core objects. Koalas mirrors much of pandas while executing on Spark, so APIs that look local can still trigger distributed Spark jobs or driver collection.

## Imports and object model

```python
import pandas as pd
import databricks.koalas as ks
```

Core public objects:

- `ks.DataFrame(data=None, index=None, columns=None, dtype=None, copy=False)`
- `ks.Series(data=None, index=None, dtype=None, name=None, copy=False, fastpath=False)`
- `ks.Index`, `ks.Int64Index`, `ks.Float64Index`, `ks.CategoricalIndex`, `ks.DatetimeIndex`, `ks.MultiIndex`
- `ks.from_pandas(pobj)` converts a pandas `DataFrame`, `Series`, or `Index` into the corresponding Koalas object.
- `DataFrame.to_pandas()` and `Series.to_pandas()` collect to pandas on the driver. Treat this as an explicit bounded-data operation.
- `DataFrame.to_spark(index_col=None)` returns a Spark DataFrame. If `index_col` is set, Koalas materializes the index as one or more Spark columns.

Koalas objects keep pandas-style logical index and column labels plus hidden Spark columns for index/order bookkeeping. Spark DataFrames do not natively have an index, so Spark-to-Koalas conversion may create a default index unless an explicit `index_col` is supplied.

## Constructors and top-level functions

| API | Use | Notes |
| --- | --- | --- |
| `ks.DataFrame(data, index=None, columns=None, dtype=None)` | Build a Koalas frame from dict/list/NumPy/pandas/Spark input. | If `data` is pandas, Spark, or Koalas `Series`, do not pass other constructor arguments. |
| `ks.Series(data, index=None, dtype=None, name=None)` | Build a single Koalas column. | For local literals, use tiny fixtures or bounded test data. |
| `ks.from_pandas(pobj)` | Migrate pandas `DataFrame`, `Series`, or `Index`. | Keeps pandas index metadata logically in Koalas. |
| `ks.range(start, end=None, step=1, num_partitions=None)` | Create a one-column frame named `id`. | Good for smoke checks and examples. |
| `ks.concat(objs, axis=0, join="outer", ignore_index=False, sort=False)` | Concatenate frames/series. | Duplicate labels can cause ambiguity; normalize before concat. |
| `ks.merge(left, right, how="inner", on=None, left_on=None, right_on=None, left_index=False, right_index=False, suffixes=("_x", "_y"))` | SQL-style join with pandas-like syntax. | `DataFrame.merge` has the same core signature; route deep join/Spark optimization questions to Spark IO/SQL. |
| `ks.melt(frame, id_vars=None, value_vars=None, var_name=None, value_name="value")` | Wide-to-long reshape. | Validate that `id_vars` and `value_vars` names are unique. |
| `ks.get_dummies(data, prefix=None, prefix_sep="_", dummy_na=False, columns=None, sparse=False, drop_first=False, dtype=None)` | One-hot encode categorical columns. | Returns a Koalas `DataFrame`; avoid duplicate generated names. |
| `ks.to_datetime(arg, errors="raise", format=None, unit=None, infer_datetime_format=False, origin="unix")` | Convert scalar/list/Series/DataFrame-like data to datetime. | Prefer explicit `format` for predictable parsing. |
| `ks.date_range(start=None, end=None, periods=None, freq=None, tz=None, normalize=False, name=None, closed=None, **kwargs)` | Build a `DatetimeIndex`. | Time zone support is more limited than pandas. |
| `ks.to_numeric(arg)` | Numeric conversion. | Use for Series-like conversion; mixed-type columns can fail during Spark inference. |
| `ks.isna` / `isnull` / `notna` / `notnull` | Missing-value predicates. | Methods also exist on DataFrame/Series/Index. |

## DataFrame API coverage

Frequently useful DataFrame attributes:

- Metadata: `index`, `columns`, `dtypes`, `shape`, `axes`, `ndim`, `size`, `empty`, `select_dtypes`, `values`.
- Conversion/copy: `copy`, `astype`, `to_pandas`, `to_spark`, `to_numpy`, `to_dict`, `to_records`, `to_json`, `to_html`, `to_string`.
- Indexing: `loc`, `iloc`, `at`, `iat`, `head`, `tail`, `items`, `iteritems`, `keys`, `pop`, `get`, `xs`, `where`, `mask`, `query`.
- Arithmetic/comparison: `add`, `sub`, `mul`, `div`, `truediv`, `floordiv`, `mod`, `pow`, reflected variants, `lt`, `le`, `gt`, `ge`, `eq`, `ne`, `dot`.
- Descriptive stats: `abs`, `all`, `any`, `count`, `describe`, `max`, `min`, `mean`, `median`, `sum`, `std`, `var`, `sem`, `skew`, `kurt`, `corr`, `quantile`, `nunique`, `pct_change`, cumulative methods, `round`, `diff`, `eval`.
- Label/selection: `drop`, `drop_duplicates`, `duplicated`, `rename`, `rename_axis`, `reset_index`, `set_index`, `filter`, `isin`, `sample`, `take`, `truncate`, `first`, `last`, `swaplevel`, `droplevel`.
- Missing data: `dropna`, `fillna`, `replace`, `bfill`, `ffill`, `backfill`, `pad`, `isna`, `isnull`, `notna`, `notnull`.
- Reshaping/sorting: `sort_index`, `sort_values`, `pivot`, `pivot_table`, `melt`, `stack`, `unstack`, `explode`, `squeeze`, `transpose` / `T`, `reindex`, `rank`.
- Combining: `assign`, `append`, `merge`, `join`, `update`, `insert`.

Route `apply`, `transform`, `applymap`, `map_in_pandas`, `groupby`, `rolling`, and `expanding` depth to `apply-groupby-window`.
Route storage-oriented conversion and `.spark` accessor depth to `spark-io-sql`.

## Series API coverage

Frequently useful Series attributes and methods:

- Metadata: `index`, `dtype`, `dtypes`, `name`, `shape`, `axes`, `ndim`, `size`, `empty`, `hasnans`, `values`, `T`.
- Conversion: `astype`, `copy`, `to_pandas`, `to_numpy`, `to_list`, `to_dict`, `to_frame`, `to_string`, `to_json`, `to_csv`, `to_excel`.
- Indexing: `loc`, `iloc`, `at`, `iat`, `head`, `tail`, `items`, `iteritems`, `keys`, `pop`, `get`, `xs`, `where`, `mask`.
- Descriptive stats: `abs`, `all`, `any`, `between`, `clip`, `count`, `describe`, `max`, `min`, `mean`, `median`, `mode`, `sum`, `std`, `var`, `sem`, `skew`, `kurt`, `corr`, `quantile`, `nunique`, `unique`, `value_counts`, `rank`, cumulative methods, `round`, `diff`, monotonicity checks.
- Label/selection: `drop`, `drop_duplicates`, `rename`, `rename_axis`, `reset_index`, `reindex`, `sort_index`, `sort_values`, `isin`, `sample`, `take`, `truncate`, `first`, `last`, `idxmax`, `idxmin`.
- Missing data: `dropna`, `fillna`, `bfill`, `ffill`, `backfill`, `pad`, `isna`, `isnull`, `notna`, `notnull`.
- Combining/reshaping: `append`, `combine_first`, `replace`, `update`, `unstack`, `explode`, `repeat`, `squeeze`, `factorize`.

Route `Series.apply`, `map`, `transform`, `groupby`, `rolling`, and `expanding` depth to `apply-groupby-window` unless the task is only a basic vectorized replacement.

## Accessors

### String accessor: `Series.str`

Common methods include `capitalize`, `title`, `lower`, `upper`, `swapcase`, `startswith`, `endswith`, `contains`, `count`, `find`, `rfind`, `index`, `rindex`, `get`, `len`, `strip`, `lstrip`, `rstrip`, `slice`, `slice_replace`, `replace`, `split`, `rsplit`, `cat`, `get_dummies`, `match`, `findall`, `extract`, `extractall`, `normalize`, `pad`, `center`, `ljust`, `rjust`, `zfill`, `wrap`, `join`, `repeat`, `partition`, `rpartition`, `encode`, `decode`, `translate`, and type predicates such as `isalnum`, `isalpha`, `isdigit`, `isspace`, `islower`, `isupper`, `istitle`, `isnumeric`, and `isdecimal`.

### Datetime accessor: `Series.dt`

Common properties and methods include `date`, `year`, `month`, `day`, `hour`, `minute`, `second`, `microsecond`, `week`, `weekofyear`, `dayofweek`, `weekday`, `dayofyear`, `quarter`, `is_month_start`, `is_month_end`, `is_quarter_start`, `is_quarter_end`, `is_year_start`, `is_year_end`, `is_leap_year`, `daysinmonth`, `days_in_month`, `normalize`, `strftime`, `round`, `floor`, `ceil`, `month_name`, and `day_name`.

### Categorical accessor: `Series.cat`

Supported essentials are `categories`, `ordered`, and `codes`. Some pandas category mutators exist in source but are intentionally incomplete or may raise; for robust workflows, construct category-like values explicitly and validate with `dtype`, `cat.categories`, and `cat.codes` before relying on mutating category metadata.

## Index API coverage

Index objects support pandas-like metadata, conversion, set operations, missing-data handling, and sorting:

- `Index`: `is_monotonic`, `is_unique`, `has_duplicates`, `hasnans`, `dtype`, `shape`, `name`, `names`, `size`, `nlevels`, `values`, `all`, `any`, `argmin`, `argmax`, `copy`, `delete`, `equals`, `factorize`, `insert`, `drop`, `drop_duplicates`, `min`, `max`, `rename`, `repeat`, `take`, `unique`, `nunique`, `value_counts`, `fillna`, `dropna`, `isna`, `notna`, `astype`, `item`, `to_list`, `to_series`, `to_frame`, `to_numpy`, `sort_values`, `shift`, `append`, `intersection`, `union`, `difference`, `symmetric_difference`, `asof`, `isin`.
- `MultiIndex`: constructors `from_arrays`, `from_tuples`, `from_product`, `from_frame`; basics such as `names`, `nlevels`, `swaplevel`, `droplevel`, set operations, conversion, sorting, and value counts.
- `DatetimeIndex`: datetime fields parallel to `Series.dt`, plus `indexer_between_time`, `indexer_at_time`, `normalize`, `strftime`, `round`, `floor`, `ceil`, `month_name`, and `day_name`.
- `CategoricalIndex`: `categories`, `ordered`, and `codes`.

## Known pandas gaps and distributed semantics

- Koalas does not target 100% pandas coverage. Unsupported pandas APIs are represented by missing modules that raise `NotImplementedError` with method/property names and reasons.
- `Series` and `Index` are intentionally not locally iterable. Use vectorized methods, `apply` with type-hint guidance, or explicitly collect bounded data with `to_numpy()` / `to_pandas()`.
- `DataFrame.__iter__` iterates column labels, like pandas; it does not iterate rows.
- Some pandas APIs that require local arrays, local memory accounting, pickling, or xarray-style conversion are unsupported or discouraged.
- `DataFrame.fillna` supports common scalar/dict and forward/backward fill workflows, but column-axis fills and some `limit`/DataFrame-value combinations are not implemented.
- Several pandas-specific dtypes are limited. Koalas maps NumPy/Python types to Spark types; `pd.Timedelta`, `pd.Categorical`, `pd.CategoricalDtype`, `pd.SparseDtype`, timezone-aware pandas dtypes, unsigned integer extension dtypes, `pd.BooleanDtype`, and `pd.StringDtype` require validation in the target runtime.
- Mixed Python types in a single column can fail during Spark/Arrow type inference; normalize to one dtype before constructing a Koalas object.
