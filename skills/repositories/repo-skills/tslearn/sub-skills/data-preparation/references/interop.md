# Interoperability reference

This route owns conversion helpers that move between tslearn and other time-series packages or package-specific data layouts.

## Dependency quick check

- `pandas` is required for `sktime`, `pyflux`, and `tsfresh` conversions.
- `cesium` is required for `cesium` conversions.
- `pyts`, `seglearn`, and `stumpy` describe target layouts, but the conversion helpers themselves do not import those packages.
- `to_sklearn_dataset` is pure NumPy reshaping and has no optional dependency.

## Conversion matrix

| Helper | From | To | Requirement | Notes |
| --- | --- | --- | --- | --- |
| `to_sklearn_dataset` | tslearn | sklearn | none | Flattens `(n_ts, sz, d)` to `(n_ts, sz * d)`.
| `to_pyts_dataset` | tslearn | pyts | equal-length input | Univariate data become `(n_ts, sz)`; multivariate data become `(n_ts, d, sz)`.
| `from_pyts_dataset` | pyts | tslearn | none | Accepts 2-D or 3-D arrays.
| `to_seglearn_dataset` | tslearn | seglearn | none | Returns an object array of per-series arrays with trailing `NaN`s removed.
| `from_seglearn_dataset` | seglearn | tslearn | none | Re-pads into `(n_ts, sz, d)`.
| `to_stumpy_dataset` | tslearn | stumpy | none | Returns a Python list; univariate series become 1-D arrays, multivariate series are feature-first.
| `from_stumpy_dataset` | stumpy | tslearn | none | Accepts the list form and restores tslearn layout.
| `to_sktime_dataset` | tslearn | sktime | pandas | Returns a `DataFrame` with `dim_0`, `dim_1`, ... columns holding `pd.Series` values.
| `from_sktime_dataset` | sktime | tslearn | pandas | Expects a `DataFrame` with contiguous `dim_*` columns.
| `to_pyflux_dataset` | tslearn | pyflux | pandas | Only supports exactly one time series.
| `from_pyflux_dataset` | pyflux | tslearn | pandas | Column order is preserved.
| `to_tsfresh_dataset` | tslearn | tsfresh | pandas | Returns a flat `DataFrame` with `id`, `time`, and `dim_*` columns.
| `from_tsfresh_dataset` | tsfresh | tslearn | pandas | Groups by `id`; row order is not guaranteed.
| `to_cesium_dataset` | tslearn | cesium | cesium | Returns a list of `cesium.time_series.TimeSeries` objects.
| `from_cesium_dataset` | cesium | tslearn | cesium | Restores tslearn layout from that list.

## What to remember for each family

### sklearn

- Use this when you want to hand a tslearn dataset to a classic sklearn model or pipeline.
- It is only a reshape; it does not change values or padding.
- If you need the original feature count later, ask for `return_dim=True`.

### pyts

- Use only on equal-length dense data.
- This is the most common place to see `ValueError: All the time series in the array should be of equal lengths`.
- `from_pyts_dataset` rejects anything that is not a 2-D or 3-D array.

### seglearn and stumpy

- These helpers preserve the series list structure that those packages expect.
- The converters strip tslearn's trailing padding on the way out and restore it on the way back.

### sktime, pyflux, and tsfresh

- Build the pandas layout explicitly; do not rely on implicit column naming.
- `from_sktime_dataset` needs a DataFrame with contiguous `dim_0..dim_{d-1}` columns.
- `to_pyflux_dataset` only accepts a single time series.
- `from_tsfresh_dataset` does not promise a stable row order because it groups ids through a set.

### cesium

- The helper works with `cesium.time_series.TimeSeries` objects, not arbitrary custom containers.
- Multivariate data are stored feature-first in cesium and re-transposed on the way back.

## Safe round-trip strategy

When writing a bundled smoke check or an ad-hoc notebook, prefer this order:

1. Start from a tiny dense tslearn dataset.
2. Convert to the target format.
3. Convert back immediately.
4. Assert shape and value preservation.
5. For pandas-backed or `tsfresh` conversions, add a short sort/reindex step if ordering matters.

## Negative-path tips

- Use a ragged input for pyts conversion to trigger a clear equal-length error.
- Use a 3-D array for `from_sktime_dataset` to trigger a clear pandas/DataFrame error.
- Use a dataset with more than one series for `to_pyflux_dataset` to trigger the single-series guard.
- Use a malformed `dim_*` sequence such as `dim_0` and `dim_2` to trigger the contiguous-column check.
