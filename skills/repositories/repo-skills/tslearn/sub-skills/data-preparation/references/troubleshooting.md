# Troubleshooting

This page collects the failures that most often appear when preparing tslearn data.

## Optional dependency failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ImportError: Conversion from/to sktime cannot be performed if pandas is not installed.` | Pandas is missing. | Install pandas or use a converter that does not need it. |
| `ImportError: Conversion from/to pyflux cannot be performed if pandas is not installed.` | Pandas is missing. | Install pandas or avoid the pyflux route. |
| `ImportError: Conversion from/to tsfresh cannot be performed if pandas is not installed.` | Pandas is missing. | Install pandas or avoid the tsfresh route. |
| `ImportError: Conversion from/to cesium cannot be performed if cesium is not installed.` | Cesium is missing. | Install cesium or use another interop target. |

## Shape and validation failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ValueError: All the time series in the array should be of equal lengths` | A converter or equal-length workflow received ragged input; pyts emits this exact error, while PAA/SAX can fail earlier with a ragged-shape error. | Resample first or convert the input to a fixed length with `TimeSeriesResampler`. |
| `ValueError: Array should be made of a single time series` | `to_pyflux_dataset` received more than one series. | Slice a single sample, e.g. `X[:1]`. |
| `ValueError: X is not a valid input sktime array. A pandas DataFrame is expected.` | A NumPy array or list was passed to `from_sktime_dataset`. | Build the expected DataFrame with `dim_*` columns. |
| `ValueError: X is not a valid input sktime array. Provided dimensions are not conitiguous.` | One of the `dim_*` columns is missing, such as `dim_1`. | Rename the columns so they are contiguous: `dim_0`, `dim_1`, ... |
| A 2-D array becomes a 3-D univariate dataset unexpectedly. | `check_dims` is expanding 2-D input by design. | Add the feature axis explicitly if you meant multivariate data. |

## Feature synchronization problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ValueError: Shape mismatch between incoming data and timestamps` | The timestamp array shape does not match `X`. | Pad timestamps to the same `(n_ts, sz, d)` shape as the data. |
| `ValueError: Timestamps must be increasing for each TS` | One feature's timestamps are not monotonic. | Sort the timestamps and the associated samples before synchronizing. |
| `TypeError: list indices must be integers or slices, not tuple` | Timestamps were passed as a nested Python list instead of a dense NumPy array. | Convert timestamps to a dense `np.ndarray` of `datetime64` values first. |
| Unexpected `NaN`s remain after imputation. | `keep_trailing_nans=True` preserves variable-length padding. | Set `keep_trailing_nans=False` when you want padded tails filled too. |

## Cache and dataset-loading confusion

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `CachedDatasets` works but `UCR_UEA_datasets` appears to use a different cache location. | They are different loaders with different storage behavior. | Use `CachedDatasets` for package-bundled offline samples and `UCR_UEA_datasets` for the downloadable archive. |
| A UCR/UEA dataset is downloaded again or appears to be missing. | The cache root changed, or `use_cache=False` forced a refresh. | Check `root_dir`, `XDG_DATA_HOME`, and the `use_cache` flag. |
| Dataset loading returns `None, None, None, None`. | The archive download or parse failed. | Inspect the warning message, verify network access, or fall back to cached data. |

## Interop gotchas

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| A tsfresh round-trip looks reordered. | `from_tsfresh_dataset` groups by `id` and does not guarantee row order. | Sort or reindex the result before comparing. |
| A cesium round-trip changes layout. | Cesium stores multivariate data feature-first. | Let `from_cesium_dataset` restore tslearn layout before comparing. |
| A pyts conversion fails on a list of unequal series lengths. | The converter requires equal-length dense input. | Resample the data first. |

## Clean negative-path check

If you want a fast failure that proves the bundled helper is rejecting malformed conversion input, run:

```bash
python scripts/data_preparation_smoke.py --malformed-conversion
```

That mode is expected to raise a clear `ValueError` from the smoke helper.
