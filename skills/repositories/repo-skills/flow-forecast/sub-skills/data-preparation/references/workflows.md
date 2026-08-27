# Data Preparation Workflows

## 1. Validate A CSV Before Training

1. Confirm the file has the expected target and feature columns.
2. Normalize any timezone-aware datetime column to tz-naive values.
3. Sort by the time column if the data is not already ordered.
4. Decide whether interpolation is needed for missing values.
5. Validate that the series is long enough for `forecast_history + forecast_length`.
6. Run [scripts/validate_timeseries_csv.py](../scripts/validate_timeseries_csv.py) on the cleaned file.
7. Hand the cleaned path to the training or inference sub-skill.

## 2. Prepare A Plain Forecasting Table

Use `CSVDataLoader` when one row represents one time step and the task is next-step forecasting.

Suggested choices:

- `target_col`: list containing the target column name(s).
- `relevant_cols`: features used by the model, including the targets when the model is autoregressive.
- `scaling`: use a scikit-learn scaler when the data ranges differ strongly.
- `interpolate_param`: use when there are holes in the history.
- `sort_column`: set when the file is not already ordered.

## 3. Prepare A Temporal Forecasting Table

Use `TemporalLoader` when the model expects separate calendar or time-of-day inputs.

Common pattern:

- Build the datetime feature columns first.
- Pass those feature names in `time_feats`.
- Keep the non-temporal data in the base dataframe.
- Set `label_len` when the decoder needs a warm-up prefix.

## 4. Prepare A Multi-Series File

Use `CSVSeriesIDLoader` or `SeriesIDTestLoader` when one CSV contains many gauges or assets.

Checklist:

- Pick a stable `series_id_col`.
- Ensure each series has enough rows for the chosen history and forecast windows.
- Keep the same `relevant_cols` for every series unless you intentionally want different loaders.
- Use `return_all=True` when the downstream model expects every series at the same timestamp.

## 5. Prepare Classification Or Variable-Length Data

Use `GeneralClassificationLoader` or `VariableSequenceLength` when the task is not forecasting.

Checklist:

- Put the label source in the first dataframe column.
- For `VariableSequenceLength`, mark sequence boundaries with `series_marker_column`.
- Use `pad_length` when the downstream model needs a fixed shape.
- Set `no_scale=True` for classification unless a specific model requires scaling.

## 6. Prepare Autoencoder Data

Use `AEDataloader` when the input and target sequences should match.

Key facts:

- `forecast_length` is always 1.
- The loader returns the same sequence twice.
- `no_scale=True` is common when reconstruction fidelity matters more than scale normalization.

## 7. When The Data Lives In GCS Or USGS Feeds

- Resolve the network/credential requirements before runtime.
- Validate the schema locally first with a sample or cached file.
- Keep `gs://` and HTTP fetches out of the default smoke path.
- Do not assume remote paths are available in the private inspection environment.
