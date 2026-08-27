# Flow Forecast Data Formats

## Scope

Use this reference when preparing tabular inputs for Flow Forecast loaders. It covers the public data-shape contracts used by the package's CSV, temporal, series-id, classification, variable-length, and autoencoder loaders.

## Canonical Path Handling

`flood_forecast.preprocessing.buil_dataset.get_data()` accepts either a local path, a `gs://bucket/object.csv` URI, or an already-loaded `pandas.DataFrame`.

- Local CSV files are read with `pandas.read_csv`.
- `gs://` paths are downloaded into `data/<bucket>/<object>` before loading.
- Non-CSV paths are returned as-is, so callers should treat them as opaque asset paths.

## Datetime Normalization

Flow Forecast's CSV loaders expect sort columns to be timezone-naive `datetime64[ns]` values.

Use `to_tz_naive_datetime()` to normalize timezone-aware timestamps before sorting or slicing. This avoids the common `ValueError: cannot supply both a tz and a timezone-naive dtype` failure when input data comes from USGS, NOAA, or other UTC-aware feeds.

## Default Forecasting CSV

The default forecasting path uses `CSVDataLoader`.

### Typical shape

- Historical window: `forecast_history` rows.
- Prediction window: `forecast_length` rows.
- Input columns: `relevant_cols`, optionally extended with engineered time features.
- Target columns: `target_col`.
- Scaling: optional; if enabled, targets are scaled with a second scaler of the same class.

### Important behavior

- The loader slices the selected dataframe into a historical window and a future window.
- `scaled_cols` defaults to `relevant_cols`.
- If `sort_column` is provided, the loader converts that column to tz-naive datetimes and sorts the dataframe.
- If `interpolate_param` is provided, the loader applies the named interpolation helper before scaling.
- The loader writes a temporary `temp_df.csv` in the current working directory as part of construction.

## Temporal Forecasting

`TemporalLoader` and `TemporalTestLoader` separate temporal features from the main feature table.

### Inputs

- `time_feats`: the datetime-derived feature columns to keep separate.
- `kwargs`: the standard CSV loader parameters.
- `label_len`: the length of the decoder warm-up window used by Informer-style models.

### Outputs

- Encoder source data: main features and temporal features.
- Decoder target data: future temporal features and future main features.

### When to use

Use the temporal loaders when the model expects explicit time covariates such as hour, weekday, month, or holiday flags.

## Series-ID Forecasting

`CSVSeriesIDLoader` and `SeriesIDTestLoader` handle multi-series data where one file contains multiple independent entities.

### Inputs

- `series_id_col`: the column that identifies each time series.
- `main_params`: the base CSV loader parameters.
- `return_method`: typically `dict`.
- `return_all`: whether to load all series for each index.

### Outputs

- Training and validation loaders return dictionaries keyed by series.
- The test loader wraps each underlying series in a `CSVTestLoader` so forecasts can be aligned per series.

## Classification And Variable-Length Data

### `GeneralClassificationLoader`

Use this loader for sequence classification.

- `sequence_length` becomes the historical window.
- The first column of the dataframe is treated as the label source.
- The loader returns a sequence tensor and a one-hot label tensor.

### `VariableSequenceLength`

Use this loader when sequences are grouped by a marker column and examples have different lengths.

- `series_marker_column` defines the group boundaries.
- `task` controls whether the loader behaves like classification or autoencoding.
- `pad_length` can truncate or zero-pad sequences to a fixed length.

### `AEDataloader`

Use this loader for autoencoder-style reconstruction.

- `forecast_length` is forced to `1`.
- The input and target windows are identical sequences.
- `no_scale=True` is common because the output is reconstruction rather than forecasting.

## Public Loader Expectations

- `target_col` should be a list even for a single target.
- `relevant_cols` should include every column needed by the model, especially target columns for autoregressive or multivariate models.
- For temporal or series-id loaders, the CSV must already contain the required helper columns.
- For classification, the label column should be numeric and encode classes in the first dataframe column.

## When To Read The Next Reference

- [loader-api.md](loader-api.md) for constructor arguments and return shapes.
- [workflows.md](workflows.md) for end-to-end loader selection.
- [troubleshooting.md](troubleshooting.md) for timezone, NaN, and series-id errors.
