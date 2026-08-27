---
name: data-pipeline
description: "Prepare tabular time-series data for PyTorch Forecasting v1
  TimeSeriesDataSet, encoders, normalizers, dataloaders, serialization, and
  validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Data Pipeline Sub-skill

Use this sub-skill when the task is to turn a pandas-style tabular time-series DataFrame into PyTorch Forecasting 1.8.0 data objects for training, validation, testing, or prediction. The primary API is `pytorch_forecasting.TimeSeriesDataSet` and the v1 data utilities under `pytorch_forecasting.data`.

## Route here for

- Choosing and declaring `time_idx`, `target`, `group_ids`, static covariates, known-future covariates, unknown-future covariates, weights, lags, encoders, scalers, and target normalizers.
- Creating `TimeSeriesDataSet` objects for train/validation/test/predict workflows with `TimeSeriesDataSet.from_dataset()` or `TimeSeriesDataSet.from_parameters()`.
- Converting datasets to PyTorch dataloaders with `TimeSeriesDataSet.to_dataloader()` and understanding returned batch keys and shapes.
- Handling missing timesteps, categorical unknowns, target normalization, dataset serialization, and pre-flight DataFrame validation.

## Route away

- Model architecture selection, `.from_dataset()` model construction, checkpoint loading, and prediction API details belong in `../forecasting-models/SKILL.md`.
- Losses, metrics, quantiles, Optuna tuning, and learning-rate finder decisions belong in `../metrics-and-tuning/SKILL.md`.
- Experimental v2 `TimeSeries` and `EncoderDecoderTimeSeriesDataModule` workflows belong in `../api-v2-workflows/SKILL.md`.

## Bundled references and scripts

- Use [`references/time-series-dataset.md`](references/time-series-dataset.md) when you need the v1 `TimeSeriesDataSet` constructor contract, column-role map, train/validation/inference recipes, normalizer/encoder notes, dataloader shapes, serialization, and validation snippets.
- Use [`references/data-validation-and-troubleshooting.md`](references/data-validation-and-troubleshooting.md) when data construction fails or behaves unexpectedly; it maps symptoms to likely causes and concrete recovery steps for NaNs, gaps, short series, categorical unknowns, normalizers, and shape surprises.
- Use [`scripts/validate_timeseries_dataframe.py`](scripts/validate_timeseries_dataframe.py) before constructing a dataset from a CSV to catch missing required columns, duplicate group/time rows, target NaNs, role overlap, non-integer time indexes, sort issues, gaps, and too-short groups without importing PyTorch Forecasting.

## Minimal working pattern

```python
from pytorch_forecasting import TimeSeriesDataSet
from pytorch_forecasting.data import GroupNormalizer, NaNLabelEncoder

training = TimeSeriesDataSet(
    train_df,
    time_idx="time_idx",              # integer, increasing within each group
    target="sales",                  # continuous or categorical target column
    group_ids=["store", "sku"],      # columns that identify one series
    max_encoder_length=36,
    max_prediction_length=6,
    static_categoricals=["store", "sku"],
    time_varying_known_reals=["time_idx", "price", "promotion"],
    time_varying_unknown_reals=["sales"],
    target_normalizer=GroupNormalizer(groups=["store", "sku"], transformation="log1p"),
    categorical_encoders={"sku": NaNLabelEncoder(add_nan=True)},
)

validation = TimeSeriesDataSet.from_dataset(
    training,
    full_df,
    min_prediction_idx=train_df["time_idx"].max() + 1,
    stop_randomization=True,
)

train_loader = training.to_dataloader(train=True, batch_size=64, num_workers=0)
val_loader = validation.to_dataloader(train=False, batch_size=64, num_workers=0)
```

If a task starts from CSV, run the bundled validator first, then use the references above to construct the actual `TimeSeriesDataSet`.
