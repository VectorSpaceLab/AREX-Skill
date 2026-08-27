# API reference

This file summarizes the public helpers owned by the data-preparation route.
The common tslearn convention is a dataset shaped `(n_ts, sz, d)`, where `n_ts`
is the number of time series, `sz` is the time axis length, and `d` is the
feature dimension.

## Validation and formatting helpers

| Helper | Purpose | Important notes |
| --- | --- | --- |
| `to_time_series(ts, remove_nans=False, be=None, dtype=float)` | Format one series as `(sz, d)`. | 1-D input becomes univariate `(sz, 1)`. Trailing `NaN`s can be trimmed with `remove_nans=True`. |
| `to_time_series_dataset(dataset, dtype=float, be=None)` | Format one series or a list of series as `(n_ts, sz, d)`. | Ragged input is padded with trailing `NaN`s. Empty input becomes `(0, 0, 0)`. A pandas `DataFrame` is accepted when pandas is installed. |
| `check_variable_length_input(X)` | Validate a variable-length input before preprocessing. | Useful before resampling, imputing, or synchronizing. It returns a dense tslearn dataset. |
| `check_dims(X, X_fit_dims=None, extend=True, check_n_features_only=False)` | Validate dimensionality and optionally expand 2-D input. | 2-D input is interpreted as univariate and reshaped to 3-D when `extend=True`. |
| `check_dataset(X, force_univariate=False, force_equal_length=False, force_single_time_series=False)` | Enforce tslearn shape constraints. | Use this when a transform must reject ragged, multivariate, or multi-series input. |
| `check_equal_size(dataset, be=None)` | Check whether all series share the same effective length. | Returns `True` for an empty dataset. |
| `ts_size(ts, be=None)` | Count the effective length of one series. | Trailing all-`NaN` steps are ignored. |
| `ts_zeros(sz, d=1)` | Build a zero-filled series. | Handy as a placeholder or initial reference series. |

## Text I/O helpers

| Helper | Purpose | Important notes |
| --- | --- | --- |
| `time_series_to_str(ts, fmt="%.18e")` | Convert one series to the bundled text format. | Dimensions are separated by `|`, values by spaces. |
| `str_to_time_series(ts_str)` | Parse one series from the bundled text format. | The inverse of `time_series_to_str` for the supported layout. |
| `save_time_series_txt(fname, dataset, fmt="%.18e")` | Write a dataset to disk. | Preserves variable-length padding through the text representation. |
| `load_time_series_txt(fname)` | Read a dataset from disk. | Returns a tslearn dataset, not a pandas object. |

## Sklearn compatibility shims

| Helper | Purpose | Notes |
| --- | --- | --- |
| `check_array` | Thin wrapper around sklearn validation. | Exists to smooth sklearn API changes around `force_all_finite` / `ensure_all_finite`. |
| `check_X_y` | Thin wrapper around sklearn validation. | Use it only when you need tslearn's compatibility shim in custom code. |

## Interoperability conversions

### `sklearn`

- `to_sklearn_dataset(dataset, dtype=float, return_dim=False)` flattens
  `(n_ts, sz, d)` to `(n_ts, sz * d)`.
- Set `return_dim=True` when you need the original feature dimension back.

### `pyts`

- `to_pyts_dataset(X)` converts equal-length tslearn data to pyts layout.
  Univariate data becomes `(n_ts, sz)`; multivariate data becomes
  `(n_ts, d, sz)`.
- `from_pyts_dataset(X)` accepts 2-D or 3-D pyts arrays and returns tslearn
  format.
- Ragged input is rejected.

### `seglearn`

- `to_seglearn_dataset(X)` returns an object array of per-series arrays.
  Trailing `NaN`s are trimmed.
- `from_seglearn_dataset(X)` collects seglearn-style arrays back into a padded
  tslearn dataset.

### `stumpy`

- `to_stumpy_dataset(X)` returns a list of arrays, one per series.
  Univariate series are flattened to 1-D; multivariate series are transposed to
  feature-first layout.
- `from_stumpy_dataset(X)` accepts the list form and restores tslearn layout.

### `sktime`

- `to_sktime_dataset(X)` returns a pandas `DataFrame` with columns named
  `dim_0`, `dim_1`, ... and one `pd.Series` per cell.
- `from_sktime_dataset(X)` expects a pandas `DataFrame` with contiguous
  `dim_*` columns.
- Pandas is required for both directions.

### `pyflux`

- `to_pyflux_dataset(X)` converts exactly one time series to a pandas
  `DataFrame`.
- `from_pyflux_dataset(X)` converts the DataFrame back to a single-series
  tslearn dataset.
- Pandas is required.

### `tsfresh`

- `to_tsfresh_dataset(X)` returns a flat pandas `DataFrame` with `id`, `time`,
  and `dim_*` columns.
- `from_tsfresh_dataset(X)` groups rows by `id` and restores tslearn layout.
- Pandas is required.
- Row order is not a contract; sort or reindex if order matters.

### `cesium`

- `to_cesium_dataset(X)` returns a list of `cesium.time_series.TimeSeries`
  objects.
- `from_cesium_dataset(X)` restores tslearn layout from that list.
- Cesium is required.

## Preprocessing classes

| Class | Signature | What it does | Important notes |
| --- | --- | --- | --- |
| `TimeSeriesResampler` | `TimeSeriesResampler(sz=-1)` | Resample each series to a target length using interpolation. | If `sz <= 0`, the fitted data's longest length is used. `sz=1` collapses each series to a mean feature vector. |
| `TimeSeriesScalerMinMax` | `TimeSeriesScalerMinMax(value_range=(0., 1.), per_timeseries=True, per_feature=True)` | Scale values into a requested range. | Ignores `NaN`s when computing min/max. When `per_timeseries=False`, global statistics are learned at fit time. |
| `TimeSeriesScalerMeanVariance` | `TimeSeriesScalerMeanVariance(mu=0., std=1., per_timeseries=True, per_feature=True)` | Scale values to a requested mean and standard deviation. | Ignores `NaN`s when computing mean/std. Zero std is replaced by 1. |
| `TimeSeriesImputer` | `TimeSeriesImputer(method="mean", value=nan, keep_trailing_nans=True)` | Replace missing values. | Methods: `mean`, `median`, `ffill`, `bfill`, `linear`, `constant`, or a callable. Trailing padding can be kept or filled. |
| `TimeSeriesFeatureSynchronizer` | `TimeSeriesFeatureSynchronizer(reference_feature_index=0)` | Synchronize features onto the reference feature's temporal grid. | When timestamps are supplied, they must match `X`'s shape and be monotonic per feature. Use `np.datetime64('nat')` for missing positions. In practice, pass a dense NumPy timestamp array rather than a nested Python list. |

## Piecewise transforms

| Class | Signature | What it does | Important notes |
| --- | --- | --- | --- |
| `PiecewiseAggregateApproximation` | `PiecewiseAggregateApproximation(n_segments=1)` | Reduce each series to segment means. | Input should be dense and equal-length. `inverse_transform` expands the segments back to the original length. |
| `SymbolicAggregateApproximation` | `SymbolicAggregateApproximation(n_segments=1, alphabet_size_avg=5, scale=False)` | Quantize PAA segments into SAX symbols. | `scale=True` normalizes input before symbolization. Output is integer-coded. |
| `OneD_SymbolicAggregateApproximation` | `OneD_SymbolicAggregateApproximation(n_segments=1, alphabet_size_avg=5, alphabet_size_slope=5, sigma_l=None, scale=False)` | Extend SAX with slope symbols. | Output has `2 * d` channels: average symbols first, slope symbols second. |

## Datasets and generators

| Helper | Purpose | Important notes |
| --- | --- | --- |
| `CachedDatasets` | Access package-bundled offline datasets. | Use this for deterministic smoke checks and offline examples. |
| `UCR_UEA_datasets` | Access and cache UCR/UEA archive datasets. | `use_cache` controls refresh behavior. `root_dir` overrides the cache root. First use may download metadata and archives. |
| `extract_from_zip_url` | Download and unpack a zip archive. | Networked helper used by the dataset loader. Not a smoke-test target. |
| `in_file_string_replace` | Patch text files in place. | Used to fix known typos in downloaded dataset metadata. |
| `random_walks` | Generate synthetic random-walk series. | Returns an array with shape `(n_ts, sz, d)`. |
| `random_walk_blobs` | Generate random-walk blobs plus labels. | Returns `(X, y)`; `y` contains blob ids. |

## Shape reminders

- Use `to_time_series_dataset` before any converter or transform that expects a
  dense tslearn dataset.
- Use `TimeSeriesResampler` before PAA/SAX/1d-SAX when the data are ragged or a
  fixed length is required.
- Use `TimeSeriesImputer` before `TimeSeriesFeatureSynchronizer` when the data
  contain interior missing values.
