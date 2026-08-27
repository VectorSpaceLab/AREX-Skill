# Workflows

Use these recipes when you need to prepare tslearn data without reopening the source repository.

## 1. Normalize raw input

Use this route when the user gives you lists, ragged arrays, or a mix of plain
Python and NumPy objects.

1. Call `to_time_series_dataset` to get a dense `(n_ts, sz, d)` array.
2. Check the result with `check_equal_size`, `check_dataset`, or `ts_size` if
   you need to confirm the effective length.
3. If the input is a single series, use `to_time_series` first so you can inspect
   the 2-D `(sz, d)` form.
4. If a downstream step needs a fixed number of timestamps, resample after
   normalization.

Common pattern:

```python
from tslearn.utils import to_time_series_dataset

X = to_time_series_dataset([
    [1, 2, 3],
    [1, 2],
])
```

## 2. Repair gaps and synchronize features

Use this when a dataset has missing values, different sampling grids, or
feature-level timestamps that do not line up.

1. Convert the input to tslearn format.
2. Run `TimeSeriesImputer` to fill interior `NaN`s.
3. If features are acquired at different times, run
   `TimeSeriesFeatureSynchronizer` with a dense timestamp array.
4. If the next step needs a fixed length, run `TimeSeriesResampler`.

Recommended chain for a variable-length, timestamped multivariate dataset:

```python
from tslearn.preprocessing import (
    TimeSeriesFeatureSynchronizer,
    TimeSeriesImputer,
    TimeSeriesResampler,
)
from tslearn.utils import to_time_series_dataset

X = to_time_series_dataset(raw_series)
X = TimeSeriesImputer(method="linear", keep_trailing_nans=True).fit_transform(X)
X = TimeSeriesFeatureSynchronizer(reference_feature_index=0).fit_transform(
    X,
    timestamps=timestamps,
)
X = TimeSeriesResampler(sz=32).fit_transform(X)
```

Guidance:

- Keep trailing `NaN`s when they represent padding for variable-length data.
- Use `np.datetime64('nat')` for missing timestamps.
- Keep timestamps in a dense NumPy array with the same shape as `X`.

## 3. Load data

Use the dataset helpers when you need reusable benchmark data or local offline
samples.

- `CachedDatasets` is the fastest offline path. It ships with the package and
  includes small cached datasets such as `Trace`.
- `UCR_UEA_datasets` is for the downloadable UCR/UEA archive. It caches on
  first use and can be redirected with `root_dir`.
- If a load fails, check whether the environment has the archive cached and
  whether the cache root matches the intended location.

Practical notes:

- `CachedDatasets` is package-bundled; do not confuse it with the archive cache.
- `UCR_UEA_datasets` may access the network on first use.
- The default archive cache root follows `XDG_DATA_HOME` when set and otherwise
  falls back to `~/.tslearn/datasets/UCR_UEA`.

## 4. Generate tiny synthetic data

Use synthetic data when you need a deterministic smoke fixture or a small
example for a docstring or helper.

- `random_walks` gives one unlabeled synthetic dataset.
- `random_walk_blobs` gives both `X` and `y`.

Use a fixed random state for reproducibility.

Example:

```python
from tslearn.generators import random_walk_blobs

X, y = random_walk_blobs(n_ts_per_blob=2, sz=8, d=1, n_blobs=2, random_state=0)
```

## 5. Resample and scale

Use scaling before symbolic compression or before a model that expects values
on a comparable numeric range.

1. `TimeSeriesScalerMinMax` for bounded ranges.
2. `TimeSeriesScalerMeanVariance` for mean/std normalization.
3. `TimeSeriesResampler` when the next step needs a fixed length.

Notes:

- Both scalers ignore `NaN`s during fit-time statistics.
- `TimeSeriesResampler(sz=-1)` uses the longest fitted series length.
- `TimeSeriesResampler(sz=1)` collapses each series to one averaged step.

## 6. Compress with piecewise transforms

Use this when you want an approximate, lower-dimensional representation.

1. Make sure the input is dense and equal-length.
2. Optionally scale first if the symbolic representation should work on a
   normalized signal.
3. Fit `PiecewiseAggregateApproximation`, `SymbolicAggregateApproximation`, or
   `OneD_SymbolicAggregateApproximation`.
4. Use `inverse_transform` when you need an approximate reconstruction.

Important:

- PAA/SAX/1d-SAX do not own variable-length repair.
- Resample first if the source data are ragged or you need a common length.
- Keep distance computations in the metrics/backends route; this sub-skill only
  owns the preprocessing and symbolic transforms.

## 7. Convert formats for another package

Use `interop.md` for the exact target shape and optional dependency list.
A quick rule of thumb:

- Flatten to sklearn with `to_sklearn_dataset`.
- Convert equal-length dense data to pyts with `to_pyts_dataset`.
- Convert to/from object arrays for seglearn.
- Convert to/from lists of arrays for stumpy.
- Use pandas-backed helpers only when pandas is installed.
- Use cesium helpers only when cesium is installed.

## 8. Use the smoke helper

Run the bundled smoke helper with a Python environment that can import `tslearn`
when you need a deterministic check that the sub-skill still works after a file
change or a fresh checkout.

```bash
python scripts/data_preparation_smoke.py
```

Use the negative-path mode when you want a clean malformed-input failure:

```bash
python scripts/data_preparation_smoke.py --malformed-conversion
```
