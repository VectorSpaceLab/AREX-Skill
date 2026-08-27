# Time-Series Data Formats

`TimeSeriesPredictor` expects `TimeSeriesDataFrame` input. Build and validate that object before choosing models.

## Required Shape

A flat pandas frame or file must contain:

| Column | Required | Meaning |
| --- | --- | --- |
| `item_id` | yes | Series identifier. Each distinct value is one univariate time series. Must be string or integer and non-null. |
| `timestamp` | yes | Observation timestamp. Must be convertible to pandas datetime and non-null. |
| target, usually `target` | yes for fitting/evaluation | Numeric value to forecast. If not named `target`, pass `target="column_name"` to `TimeSeriesPredictor`. |
| known covariates | optional | Dynamic features known through the forecast horizon, such as holidays, prices, promotions, or weather forecasts. |
| past covariates | optional | Dynamic features only observed historically. AutoGluon treats non-target/non-known columns as past covariates. |

The internal index is a two-level `MultiIndex` named exactly `item_id` and `timestamp`.

## Flat DataFrame With Default Columns

```python
raw = pd.DataFrame({
    "item_id": ["store_1", "store_1", "store_2", "store_2"],
    "timestamp": ["2024-01-01", "2024-01-02", "2024-01-01", "2024-01-02"],
    "target": [10.0, 12.0, 7.0, 9.0],
})
ts_df = TimeSeriesDataFrame(raw)
```

AutoGluon converts `timestamp` to datetime and indexes by `item_id`/`timestamp`.

## Renamed ID/Timestamp Columns

Use `id_column` and `timestamp_column` when raw data uses names such as `sku` and `date`.

```python
ts_df = TimeSeriesDataFrame.from_data_frame(
    raw,
    id_column="sku",
    timestamp_column="date",
)
```

If `raw` also contains columns literally named `item_id` or `timestamp`, AutoGluon avoids collisions by renaming the old default column with a `__` prefix. Future agents should still prefer cleaning ambiguous columns before construction.

## MultiIndex DataFrame

```python
indexed = raw.rename(columns={"sku": "item_id", "date": "timestamp"})
indexed["timestamp"] = pd.to_datetime(indexed["timestamp"])
indexed = indexed.set_index(["item_id", "timestamp"])
ts_df = TimeSeriesDataFrame(indexed)
```

The MultiIndex level names must be exactly `item_id` and `timestamp`; the timestamp level must use datetime dtype.

## Files and Iterables

```python
ts_df = TimeSeriesDataFrame.from_path("series.csv")
ts_df = TimeSeriesDataFrame.from_path("series.parquet", id_column="sku", timestamp_column="date")
```

Iterable construction is compatible with GluonTS-style dictionaries:

```python
iterable = [
    {"target": [1.0, 2.0, 3.0], "start": pd.Period("2024-01-01", freq="D")},
    {"target": [4.0, 5.0, 6.0], "start": pd.Period("2024-01-01", freq="D")},
]
ts_df = TimeSeriesDataFrame.from_iterable_dataset(iterable)
```

Each iterable item must be a dictionary with `target` and a pandas `Period` `start`.

## Static Features

Static features describe item-level metadata that does not change over time.

```python
static = pd.DataFrame({
    "item_id": ["store_1", "store_2"],
    "region": ["north", "south"],
    "capacity": [100, 80],
})
ts_df = TimeSeriesDataFrame(raw, static_features=static)
ts_df.static_features["region"] = ts_df.static_features["region"].astype("category")
```

Rules:

- The static-feature index or `item_id` column must include every item in `ts_df`.
- Extra static-feature rows are subset to the `ts_df` item set.
- Static features cannot have a `MultiIndex`.
- If static features were used during `fit`, provide the same metadata at prediction time.
- Convert categorical static features to `category`, `object`, or string dtype when you do not want integer IDs interpreted as continuous features.

## Known and Past Covariates

Known covariates are dynamic features available in the future. They must be declared in the predictor constructor and supplied for prediction.

```python
predictor = TimeSeriesPredictor(
    prediction_length=7,
    known_covariates_names=["promotion", "holiday"],
)
predictor.fit(train_data)
future = predictor.make_future_data_frame(train_data)
future["promotion"] = 0
future["holiday"] = future["timestamp"].dt.weekday.isin([5, 6]).astype(int)
predictions = predictor.predict(train_data, known_covariates=future)
```

`known_covariates` must:

- Contain all columns named in `predictor.known_covariates_names`.
- Contain every required future `item_id`/`timestamp` row for the forecast horizon.
- Use a compatible frequency and item set.

Past covariates are extra columns in training data that are not the target and not declared as known covariates. They help models use historical side information but are not required in the forecast horizon.

## Frequency Handling

- Use `ts_df.freq` for a quick check. It returns a pandas-compatible frequency string or `None` for irregular data.
- Use `ts_df.infer_frequency(raise_if_irregular=True)` when you need a strict validation error.
- If data is irregular but should be regular, either set `TimeSeriesPredictor(freq="D")` or resample explicitly with `ts_df.convert_frequency("D")`.
- `convert_frequency` may introduce missing values; handle them with `fill_missing_values()` or appropriate domain-specific imputation.
- Pandas frequency aliases are normalized, for example hourly aliases may become `h` and minute aliases may become `min`.

## Length Checks

Training filters or errors often trace back to short series. As a rule of thumb:

```python
counts = ts_df.num_timesteps_per_item()
minimum_for_default_fit = 2 * prediction_length + 1
short_items = counts[counts <= minimum_for_default_fit]
```

For the default `num_val_windows=1`, series with length `<= 2 * prediction_length` are ignored. With more validation windows, the threshold increases to `(num_val_windows + 1) * prediction_length`. The predictor also keeps an internal minimum training length of `max(prediction_length + 1, 5)` for validation folds.

## Validation Script

Use the bundled validator before fitting or debugging a user dataset:

```bash
python sub-skills/time-series-forecasting/scripts/validate_timeseries_frame.py --input series.csv --prediction-length 7 --known-covariates promotion holiday
```

The script is safe by default, performs no training, and can also generate a built-in fixture when `--input` is omitted.
