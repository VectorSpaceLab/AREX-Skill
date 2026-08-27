# Data formats for GluonTS datasets

GluonTS datasets are iterables of dictionaries called `DataEntry` objects. A minimal forecasting entry has:

| Field | Typical type/shape | Notes |
| --- | --- | --- |
| `start` | `pandas.Period` for most dataset loaders | First timestamp of `target`; frequency must match the data. `ListDataset(..., use_timestamp=True)` can keep a `pandas.Timestamp` instead. |
| `target` | univariate `(T,)`; multivariate `(target_dim, T)` | Most models use this field by convention. Splitting always slices along the last axis. |
| `item_id` | string/int | Optional identifier, populated automatically for keyed pandas datasets and long dataframes. |
| `feat_static_cat` | 1-D categorical array | Optional static categorical features. |
| `feat_static_real` | 1-D real array | Optional static real-valued features. |
| `feat_dynamic_real` | `(num_features, T)` or `(num_features, T + future)` | Optional known time-varying real features. For prediction inputs these may extend through the forecast horizon. |
| `past_feat_dynamic_real` | `(num_features, T)` | Optional time-varying real features known only up to observed history. |
| `feat_dynamic_cat`, `dynamic_feat` | `(num_features, T)` | Optional file/list dataset fields; `dynamic_feat` is a legacy alias processed as dynamic real. |
| `info` | dict | Optional metadata preserved by splitters. |

A Python `list` of such dictionaries is already a valid `Dataset` protocol object if it implements `__iter__` and `__len__`, but `PandasDataset`, `ListDataset`, and `FileDataset` normalize common inputs and validate important fields.

## PandasDataset

Import:

```python
from gluonts.dataset.pandas import PandasDataset
```

Installed signature summary:

```python
PandasDataset(
    dataframes,
    target="target",
    feat_dynamic_real=None,
    past_feat_dynamic_real=None,
    timestamp=None,
    freq=None,
    static_features=None,
    future_length=0,
    unchecked=False,
    assume_sorted=False,
    dtype=np.float32,
)
```

Accepted `dataframes` shapes:

| Input shape | Meaning | Resulting item ids |
| --- | --- | --- |
| single `pd.Series` | one univariate series; series name is not required if `target` defaults | no `item_id` |
| single `pd.DataFrame` | one series, with target/features in columns | no `item_id` |
| sized iterable of `Series` or `DataFrame` objects | multiple series | no `item_id` unless each element is a pair |
| iterable of `(item_id, Series/DataFrame)` pairs | multiple named series | pair key becomes `item_id` |
| dict of `item_id -> Series/DataFrame` | multiple named series | dict key becomes `item_id` |

Key rules:

- If using the index as time, the index should be a `PeriodIndex` or convertible to one. If `freq` is omitted, GluonTS infers it from the first index; pass `freq` explicitly when inference is ambiguous.
- If using a `timestamp` column instead of the dataframe index, pass `freq`; the constructor asserts that `freq` is supplied with `timestamp`.
- `target` can be a string for one target column or a list of column names for multivariate target arrays. Multivariate targets are transposed to `(target_dim, T)`.
- `feat_dynamic_real` columns become a 2-D array shaped `(num_features, T)`.
- `past_feat_dynamic_real` columns also become `(num_features, T)`, but if `future_length > 0`, the last `future_length` observations are removed from `target` and `past_feat_dynamic_real` while `feat_dynamic_real` can retain known future values.
- Rows are sorted by the time index unless `assume_sorted=True`.
- By default the constructor checks that each time index is uniformly spaced. Use `unchecked=True` only after separately proving uniformity.
- `static_features` is a dataframe indexed by the same item ids used in `dataframes`. Numeric columns become `feat_static_real`; categorical dtype columns become `feat_static_cat`; object dtype columns are ignored with a warning.

## Long dataframes

Use `PandasDataset.from_long_dataframe` when several items are stored in one table with an item-id column:

```python
PandasDataset.from_long_dataframe(
    dataframe=df,
    item_id="item_id",
    timestamp="timestamp",          # optional if the index is already datetime-like
    target="target",
    freq="D",
    feat_dynamic_real=["price"],
    past_feat_dynamic_real=["observed_covariate"],
    static_feature_columns=["segment", "scale"],
)
```

Installed signature summary:

```python
PandasDataset.from_long_dataframe(
    dataframe,
    item_id,
    timestamp=None,
    static_feature_columns=None,
    static_features=pd.DataFrame(),
    **kwargs,
)
```

Long-dataframe rules:

- The method groups rows by `item_id` and returns a `PandasDataset` with one `DataEntry` per item.
- If `timestamp` is provided, it is converted with `pd.to_datetime`; otherwise the existing index must be datetime-like or convertible to datetimes.
- The method uses a shallow copy and does not mutate the caller's dataframe index.
- `static_feature_columns` must be constant per item after duplicate rows are dropped; changing values within an item violate the static-feature contract.
- Categorical static columns should use pandas `category` dtype before construction. Numeric static columns are real-valued static features. Object dtype static columns are ignored.
- `static_features` can provide an additional dataframe indexed by item ids; it is concatenated with static columns collected from the long dataframe.

## ListDataset and FileDataset

Import:

```python
from gluonts.dataset.common import ListDataset, FileDataset
```

`ListDataset(data_iter, freq, one_dim_target=True, use_timestamp=False, translate=None)` materializes and normalizes an iterable of dictionaries.

- Required: `start` and `target`.
- `start` is parsed as `pd.Period(start, freq)` unless `use_timestamp=True`, in which case it becomes `pd.Timestamp(start)`.
- With `one_dim_target=True`, `target` must be one-dimensional. Set `one_dim_target=False` for multivariate target arrays.
- Static fields must be 1-D. Dynamic fields must be 2-D; one-dimensional dynamic fields are not silently accepted.
- `feat_static_cat` and `feat_dynamic_cat` are converted to integer arrays; real-valued fields become float arrays.
- `translate` can remap custom field names before validation.

`FileDataset(path, freq, one_dim_target=True, cache=False, use_timestamp=False, loader_class=None, pattern="*", levels=2, translate=None, ignore_hidden=True)` loads a file or directory of files and applies the same processing as `ListDataset`.

Supported inferred file families:

| File family | Suffixes | Dependency | Notes |
| --- | --- | --- | --- |
| JSON Lines | `.json`, `.jsonl`, `.json.gz`, `.jsonl.gz` | base package | One JSON object per line, commonly with `start` and `target`. Gzip is supported. |
| Arrow stream/file | `.arrow`, `.feather` | optional `pyarrow` / GluonTS `arrow` extra | Inferred only when the optional Arrow module imports successfully. |
| Parquet | `.parquet` | optional `pyarrow` / GluonTS `arrow` extra | Also inferred through the Arrow file wrapper. |

Directory loading notes:

- Hidden files are ignored by default.
- Non-loadable files are skipped with a warning; if no loadable files remain, `FileDataset` asserts.
- If several loadable files are found, GluonTS returns a flattened `DatasetCollection`.
- `cache=True` materializes entries after the first pass; keep it off for very large datasets unless repeated iteration is more important than memory.
- `loader_class` overrides suffix inference when a custom reader is needed.

## JSON Lines and writers

For GluonTS JSON Lines, write one object per line:

```json
{"start": "2024-01-01", "target": [1.0, 2.0, 3.0]}
{"start": "2024-01-02", "target": [4.0, 5.0, 6.0], "feat_static_cat": [1]}
```

`JsonLinesWriter(use_gzip=True, suffix=".json")` can write datasets to a file or folder. It encodes `pd.Period`, datetimes, numpy arrays, and common numeric values into JSON-compatible forms. Prefer finite numeric values in model-ready files; special values such as NaN or Infinity require explicit downstream handling.

## Optional Arrow data path

When `pyarrow` is installed, `gluonts.dataset.arrow` provides:

- `ArrowWriter(stream=False or True, suffix=".feather")`
- `ParquetWriter(suffix=".parquet")`
- `File.infer(path)` returning an Arrow, Arrow-stream, or Parquet reader based on file contents

Arrow readers preserve arrays, support slicing/indexing for file-backed formats, and can expose metadata such as `freq` when written with metadata. Because Arrow support is optional, keep Arrow workflows guarded by an import check and provide a JSON Lines fallback when sharing a skill or script with unknown environments.

## Zebras time-frame helpers

`gluonts.zebras` is a lower-level in-memory data-frame/time-series layer used in GluonTS internals and advanced pipelines. Useful entry points include:

- `zebras.time_series(values, start="2024-01-01", freq="D")` for a `TimeSeries` with an index.
- `zebras.time_frame(columns, start=..., freq=...)` or `zebras.from_pandas(df)` for a `TimeFrame`.
- `TimeFrame.split(...)` and `TimeFrame.rolsplit(...)` for past/future frame pairs.
- `zebras.schema.Schema(...).load_timeframe(...)` or `.load_splitframe(...)` for shape-checked dictionaries.

For public forecasting workflows, prefer GluonTS `Dataset` objects unless existing code specifically expects zebras objects.
