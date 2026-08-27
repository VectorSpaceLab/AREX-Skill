# Loader API Reference

## CSVDataLoader

`CSVDataLoader(file_path, forecast_history, forecast_length, target_col, relevant_cols, scaling=None, start_stamp=0, end_stamp=None, gcp_service_key=None, interpolate_param=False, sort_column=None, scaled_cols=None, feature_params=None, no_scale=False, preformatted_df=False)`

### Notes

- Accepts a local path, `gs://` URI, or `pandas.DataFrame` through `get_data()`.
- `sort_column` is normalized to tz-naive datetimes before sorting.
- `interpolate_param` is applied before scaling.
- `scaled_cols` defaults to `relevant_cols`.
- `__getitem__` returns `(src, trg)` tensors.

## CSVTestLoader

`CSVTestLoader(df_path, forecast_total, use_real_precip=True, use_real_temp=True, target_supplied=True, interpolate=False, sort_column_clone=None, **kwargs)`

### Notes

- Returns historical tensors plus the unscaled dataframe slice covering the full test window.
- `get_from_start_date()` aligns a forecast window to a datetime stamp.
- `convert_real_batches()` is a helper for chunking real-valued series.

## AEDataloader

`AEDataloader(file_path, relevant_cols, scaling=None, start_stamp=0, target_col=None, end_stamp=None, unsqueeze_dim=1, interpolate_param=False, forecast_history=1, no_scale=True, sort_column=None)`

### Notes

- Forces `forecast_length=1`.
- Returns reconstruction pairs where source and target are the same sequence.
- `get_from_start_date()` supports datetime lookup.

## GeneralClassificationLoader

`GeneralClassificationLoader(params, n_classes=2)`

### Notes

- Expects `params["sequence_length"]`.
- Rewrites the config to use `forecast_history = sequence_length` and `forecast_length = 1`.
- Returns a feature sequence and a one-hot label tensor.

## TemporalLoader

`TemporalLoader(time_feats, kwargs, label_len=0)`

### Notes

- Splits temporal features from the main feature table.
- Returns `((src_data, temporal_feats), (tar_temp, trg_data))`.
- `label_len` controls the decoder warm-up prefix.

## TemporalTestLoader

`TemporalTestLoader(time_feats, kwargs={}, decoder_step_len=None)`

### Notes

- Wraps `CSVTestLoader` while preserving temporal features.
- Returns encoder data, decoder data, the unscaled dataframe slice, and the target start index.

## CSVSeriesIDLoader

`CSVSeriesIDLoader(series_id_col, main_params, return_method, return_all=True)`

### Notes

- Builds one loader per series ID.
- Returns dictionary-like series batches.
- Useful when a single file contains many independent gauges, stations, or assets.

## SeriesIDTestLoader

`SeriesIDTestLoader(series_id_col, main_params, return_method, forecast_total=336, return_all=True)`

### Notes

- Wraps `CSVTestLoader` per series.
- `get_from_start_date_all()` aligns the same forecast start across all series.

## VariableSequenceLength

`VariableSequenceLength(series_marker_column, csv_loader_params, pad_length=None, task="classification", n_classes=9 + 90)`

### Notes

- Groups rows by `series_marker_column`.
- Supports `task="classification"` and `task="auto"`.
- `pad_length` can make sequence lengths uniform.

## Helper Functions

### `to_tz_naive_datetime(series)`

Normalizes timezone-aware timestamps into timezone-naive `datetime64[ns]` values.

### `get_data(file_path, gcp_service_key=None)`

Loads a CSV, downloads a `gs://` object to the local cache, or returns an unmodified non-CSV path.

### `preprocess_da_rnn.make_data(...)`

Builds a DA-RNN preprocessing container with fields named `features` and `targets` in this snapshot. `flood_forecast.da_rnn.train_da` expects the older custom type with fields named `feats` and `targs`, so adapt the object before passing it to `train_da.da_rnn()`:

```python
from flood_forecast.da_rnn.custom_types import TrainData as DaTrainData
from flood_forecast.preprocessing.preprocess_da_rnn import make_data

raw = make_data("data.csv", target_col=["height"], test_length=3, relevant_cols=["temp", "precip"])
train_data = DaTrainData(raw.features, raw.targets)
```

## Shape Summary

| Loader | Source shape | Target shape | Notes |
|---|---|---|---|
| `CSVDataLoader` | historical window of selected columns | future window of selected columns | most forecasting workflows |
| `CSVTestLoader` | historical window | unscaled dataframe slice + target index | forecast alignment helper |
| `AEDataloader` | reconstruction window | same reconstruction window | autoencoders |
| `GeneralClassificationLoader` | sequence window without the first label column | one-hot label | classification |
| `TemporalLoader` | main features + temporal features | decoder temporal features + decoder main features | Informer-style workflows |
| `CSVSeriesIDLoader` | one window per series | series-wise target window | multi-series data |
| `VariableSequenceLength` | grouped sequence | grouped sequence or class label | variable-length datasets |
