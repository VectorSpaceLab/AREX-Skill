# TimeSeriesDataSet Operating Guide

This guide is for PyTorch Forecasting 1.8.0 v1 data preparation. It assumes a pandas `DataFrame` with one row per observed time point per series and prepares `pytorch_forecasting.TimeSeriesDataSet` objects for downstream models.

## Core contract

`TimeSeriesDataSet` is the central v1 data object. It stores data metadata, fits categorical encoders and continuous scalers, normalizes targets, builds an index of encoder/decoder subsequences, and exposes `to_dataloader()` for model training or prediction.

Essential invariants:

- `time_idx` must name an integer-typed column. Values should increase by one within each group when there are no missing timesteps.
- `target` names the forecast target column, or a list of target columns for multi-target forecasting.
- `group_ids` names one or more columns that uniquely identify a time series together with `time_idx`.
- One `(group_ids..., time_idx)` combination should correspond to at most one row.
- Actual `NaN`/infinite values are not generally accepted after encoding/scaling. Fill real-valued NaNs before construction and add a separate missingness indicator if useful.
- Column names must not contain `.` and must not collide with protected internal names such as `__time_idx__`, `__target__<target>`, `relative_time_idx`, `encoder_length`, or generated lag names.
- Categoricals should be string or pandas categorical with non-numeric categories; numeric codes should be converted to strings if the column is categorical.

## Constructor role map

Typical import block:

```python
from pytorch_forecasting import TimeSeriesDataSet
from pytorch_forecasting.data import (
    EncoderNormalizer,
    GroupNormalizer,
    MultiNormalizer,
    NaNLabelEncoder,
    TorchNormalizer,
)
```

Constructor skeleton:

```python
dataset = TimeSeriesDataSet(
    data,
    time_idx="time_idx",
    target="target",
    group_ids=["series_id"],
    weight=None,
    max_encoder_length=30,
    min_encoder_length=None,
    min_prediction_idx=None,
    max_prediction_length=1,
    min_prediction_length=None,
    static_categoricals=None,
    static_reals=None,
    time_varying_known_categoricals=None,
    time_varying_known_reals=None,
    time_varying_unknown_categoricals=None,
    time_varying_unknown_reals=None,
    variable_groups=None,
    constant_fill_strategy=None,
    allow_missing_timesteps=False,
    lags=None,
    add_relative_time_idx=False,
    add_target_scales=False,
    add_encoder_length="auto",
    target_normalizer="auto",
    categorical_encoders=None,
    scalers=None,
    randomize_length=False,
    predict_mode=False,
)
```

Role guidance:

| Argument | Meaning | Common choice |
|---|---|---|
| `time_idx` | Integer time coordinate used to order rows and form encoder/decoder windows. | A dense integer such as `0, 1, 2, ...`; keep calendar dates in a separate covariate if needed. |
| `target` | Forecast target column name, or list for multi-target. | Include a continuous target in `time_varying_unknown_reals`; include a categorical target in `time_varying_unknown_categoricals`. |
| `group_ids` | Series identity columns. | One constant id for a single series, or multiple ids such as `store`, `sku`. |
| `static_categoricals` | Categorical covariates that do not change within a series. | IDs, segment labels, item category. A `group_id` may also be listed here when useful to the model. |
| `static_reals` | Real-valued covariates that do not change within a series. | Store size, latitude, long-term item statistic. |
| `time_varying_known_*` | Covariates known for encoder and decoder/future time. | Calendar features, planned price, planned promotion, `time_idx`. |
| `time_varying_unknown_*` | Covariates observed only up to prediction time. | Target, demand-related observations, sensor values not known in future. |
| `weight` | Optional per-row training weight column. | Use when some observations should contribute more/less to loss. |
| `variable_groups` | Maps one logical categorical variable to multiple columns. | Overlapping holiday indicator columns encoded under one variable name. |
| `lags` | Adds lagged versions of variables. | `{"sales": [7, 14]}`; every lag must be positive and no larger than the shortest usable series. |
| `constant_fill_strategy` | Constants used for generated missing timestep rows. | `{"sales": 0.0}` when unobserved demand means zero. |
| `allow_missing_timesteps` | Allows gaps in integer `time_idx` rows and fills them on the fly. | Set `True` only for missing rows, not actual NaNs. |

## Minimal single-target training dataset

```python
training = TimeSeriesDataSet(
    train_df,
    time_idx="time_idx",
    target="sales",
    group_ids=["store", "sku"],
    max_encoder_length=36,
    max_prediction_length=6,
    static_categoricals=["store", "sku"],
    time_varying_known_reals=["time_idx", "price", "promotion"],
    time_varying_unknown_reals=["sales"],
    target_normalizer=GroupNormalizer(groups=["store", "sku"], transformation="log1p"),
)
```

Use a sufficiently long `max_encoder_length` to cover important seasonality but avoid very large values for first experiments. Encoder lengths much longer than a few hundred and decoder lengths much longer than the direct business horizon can make dataset construction and training slow.

## Train/validation/test workflow

Fit encoders, scalers, and target normalizers on the training dataset, then copy those parameters into validation/test datasets:

```python
max_encoder_length = 36
max_prediction_length = 6
training_cutoff = data["time_idx"].max() - max_prediction_length

training = TimeSeriesDataSet(
    data[data.time_idx <= training_cutoff],
    time_idx="time_idx",
    target="sales",
    group_ids=["store", "sku"],
    max_encoder_length=max_encoder_length,
    max_prediction_length=max_prediction_length,
    static_categoricals=["store", "sku"],
    time_varying_known_reals=["time_idx", "price", "promotion"],
    time_varying_unknown_reals=["sales"],
    randomize_length=False,
)

validation = TimeSeriesDataSet.from_dataset(
    training,
    data,
    min_prediction_idx=training_cutoff + 1,
    stop_randomization=True,
)

train_loader = training.to_dataloader(train=True, batch_size=64, num_workers=0)
val_loader = validation.to_dataloader(train=False, batch_size=64, num_workers=0)
```

Key points:

- `from_dataset(training, data, ...)` calls `training.get_parameters()` and then constructs a new dataset with the same fitted encoders/scalers/normalizer.
- `stop_randomization=True` disables randomized encoder/decoder lengths and is recommended for validation/test.
- `min_prediction_idx` controls the earliest decoder time in the new dataset.
- `predict=True` creates one prediction sample per group using the last available decoder window.

## Inference dataset from trained parameters and future known covariates

For production-style prediction, keep the fitted training dataset or persist its parameters. New inference data must include enough encoder history for each group plus future rows for the decoder horizon. Known-future covariates must be populated for those future rows.

```python
# After training or loading a saved training dataset:
params = training.get_parameters()

# inference_df contains historical target rows plus future horizon rows.
# It must include group_ids, integer time_idx, target column, and every known covariate column.
# Unknown future covariates can be placeholders if the model will ignore decoder-side values.
predict_ds = TimeSeriesDataSet.from_parameters(
    params,
    inference_df,
    predict=True,
    stop_randomization=True,
)

predict_loader = predict_ds.to_dataloader(train=False, batch_size=128, num_workers=0)
```

Checklist for future inference rows:

1. For each group, include at least `max_encoder_length` historical rows when possible. Shorter histories may be allowed only if `min_encoder_length` permits them.
2. Include the next `max_prediction_length` future `time_idx` values for each group when you want full-horizon prediction.
3. Fill every `time_varying_known_categoricals` and `time_varying_known_reals` column on future rows.
4. Keep `group_ids` values consistent with training. If new groups or categories are expected, use `NaNLabelEncoder(add_nan=True)` for the affected categorical/group columns when fitting the training dataset.
5. Do not refit encoders/scalers on inference data. Use `from_dataset()` or `from_parameters()`.

## Categorical encoders and unknown categories

Default categorical encoding behaves like a fitted label encoder. Unknown categories at validation or inference can raise errors. Use `NaNLabelEncoder(add_nan=True)` on columns where unknowns are expected:

```python
training = TimeSeriesDataSet(
    train_df,
    time_idx="time_idx",
    target="sales",
    group_ids=["store", "sku"],
    max_encoder_length=36,
    max_prediction_length=6,
    static_categoricals=["store", "sku"],
    time_varying_known_categoricals=["holiday_name"],
    time_varying_known_reals=["time_idx"],
    time_varying_unknown_reals=["sales"],
    categorical_encoders={
        "store": NaNLabelEncoder(add_nan=True),
        "sku": NaNLabelEncoder(add_nan=True),
        "holiday_name": NaNLabelEncoder(add_nan=True),
    },
)
```

`NaNLabelEncoder(add_nan=True)` reserves encoded class `0` for NaN/unknown categories. It is useful for cold-start categories, but it does not invent meaningful embeddings; the model still has limited information about truly new categories.

## Target normalizers

`target_normalizer="auto"` chooses a normalizer from target type and sequence lengths:

- Categorical target: `NaNLabelEncoder()`.
- Real target with `max_encoder_length > 20` and `min_encoder_length > 1`: `EncoderNormalizer(...)`.
- Other real target: `GroupNormalizer(...)`.
- Positive skewed real targets can use a log-style transformation; positive less-skewed targets can use a ReLU-style transformation; non-positive targets use no transformation.

Manual choices:

```python
# Per-group scaling, common for many retail and panel datasets.
target_normalizer = GroupNormalizer(groups=["store", "sku"], transformation="log1p")

# Per-window scaling, useful when groups have strong level shifts and enough encoder history.
target_normalizer = EncoderNormalizer(transformation="relu")

# No scaling, but still follows the normalizer API.
target_normalizer = TorchNormalizer(method="identity")  # or pass target_normalizer=None

# Multiple targets require one normalizer per target.
target_normalizer = MultiNormalizer([
    GroupNormalizer(groups=["store"]),
    EncoderNormalizer(),
])
```

Notes:

- `EncoderNormalizer` is only valid when `min_encoder_length` is sufficiently large; use at least `min_encoder_length=2`.
- Multi-target `target=[...]` requires a `MultiNormalizer` unless the automatic selection produces one.
- If `add_target_scales=True`, continuous target center/scale features are added to static reals. Categorical targets do not get target-scale features.
- For count-like positive targets, a transformation such as `"log1p"`, `"log"`, `"relu"`, or `"softplus"` can improve training stability, but ensure inverse-transformed predictions are meaningful for the use case.

## Missing timesteps versus missing values

There are two different problems:

- Missing timestep rows: a group has `time_idx` values such as `1, 2, 4, 5`; row `3` is absent. Use `allow_missing_timesteps=True` if you want the dataset to generate rows on the fly. Use `constant_fill_strategy` for columns that need specific generated values; otherwise forward-fill behavior is used where applicable.
- Missing values: a row exists but a declared column contains `NaN` or infinite values. Fill these before constructing `TimeSeriesDataSet`, or for categorical columns explicitly fit with `NaNLabelEncoder(add_nan=True)` when that behavior is desired.

Example:

```python
training = TimeSeriesDataSet(
    data,
    time_idx="time_idx",
    target="demand",
    group_ids=["item"],
    max_encoder_length=28,
    max_prediction_length=7,
    time_varying_known_reals=["time_idx", "price"],
    time_varying_unknown_reals=["demand"],
    allow_missing_timesteps=True,
    constant_fill_strategy={"demand": 0.0},
)
```

If dataset construction says `Time difference between steps has been identified as larger than 1 - set allow_missing_timesteps=True`, either fill the missing rows yourself or set `allow_missing_timesteps=True` intentionally.

## Dataloader behavior and batch keys

`to_dataloader(train=True, batch_size=64, batch_sampler=None, **kwargs)` returns a PyTorch `DataLoader`. Important defaults:

- `train=True` enables shuffling and drops the last incomplete batch when the dataset length exceeds the batch size.
- `train=False` is appropriate for validation, testing, prediction, and deterministic inspection.
- `batch_sampler="synchronized"` aligns first decoder time across samples. It does not support missing timesteps and is only useful for models or analysis that need synchronized decoder time.
- You may pass ordinary `DataLoader` kwargs such as `num_workers=0`, `pin_memory=True`, or `persistent_workers=True` when appropriate.

A batch is `(x, y)`. `x` is a dictionary; `y` is `(target, weight)`.

Common `x` keys:

- `encoder_cat`: encoded categorical features, shape `(batch, encoder_time, n_categorical_features)`.
- `encoder_cont`: scaled continuous features, shape `(batch, encoder_time, n_real_features)`.
- `encoder_target`: unscaled continuous target or encoded categorical target for encoder history.
- `encoder_lengths`: actual encoder length per sample.
- `decoder_cat`: decoder categorical features, shape `(batch, decoder_time, n_categorical_features)`.
- `decoder_cont`: decoder continuous features, shape `(batch, decoder_time, n_real_features)`.
- `decoder_target`: decoder target values, useful for training/validation.
- `decoder_lengths`: actual decoder length per sample.
- `decoder_time_idx`: decoder time index values.
- `groups`: encoded group ids.
- `target_scale`: target normalizer parameters, or a list for multi-target.

Quick sanity check:

```python
x, y = next(iter(training.to_dataloader(train=False, batch_size=4, num_workers=0)))
assert x["encoder_cont"].shape[-1] == len(training.reals)
assert x["encoder_cat"].shape[-1] == len(training.flat_categoricals)
assert y[1] is None or y[1].shape == y[0].shape
```

For multi-target datasets, target-like entries can be lists/tuples, one tensor per target.

## Serialization and parameter reuse

Options:

```python
# Save the whole dataset object.
training.save("training_dataset.pt")
loaded_training = TimeSeriesDataSet.load("training_dataset.pt")

# Save only constructor parameters, encoders, scalers, and normalizer references.
params = training.get_parameters()
new_ds = TimeSeriesDataSet.from_parameters(params, new_df, predict=True, stop_randomization=True)
```

Use whole-dataset serialization when you need exact reload of the fitted dataset object. Use `get_parameters()` when you want a smaller handoff for future validation/test/prediction data. Treat saved parameters as tied to the fitted training column schema and categorical/normalizer configuration.

## Validation checklist before construction

1. Confirm all required columns exist: `time_idx`, all `target` columns, all `group_ids`, all declared covariates, and `weight` if used.
2. Confirm `time_idx` is integer typed; convert date columns to a dense integer index separately.
3. Confirm no duplicate `(group_ids..., time_idx)` rows.
4. Sort by `group_ids + [time_idx]` for reproducible debugging, even though the dataset sorts internally.
5. Decide whether gaps in `time_idx` are allowed. If not, fill missing rows before construction. If yes, set `allow_missing_timesteps=True` and provide `constant_fill_strategy` where forward fill is not semantically correct.
6. Fill real-valued NaNs and infinite values. Convert categorical numeric codes to strings. Configure `NaNLabelEncoder(add_nan=True)` for categorical unknowns you expect later.
7. Check each group is long enough for `min_encoder_length + min_prediction_length + max_lag` after filtering by `min_prediction_idx`.
8. For validation/test/inference, create datasets with `from_dataset()` or `from_parameters()` rather than a fresh constructor so encoders, scalers, and target normalizers remain identical to training.
9. Inspect one non-training dataloader batch with `num_workers=0` before running expensive training.

## CSV pre-flight command

Use the bundled validator from this sub-skill before constructing a dataset from CSV:

```bash
python scripts/validate_timeseries_dataframe.py data.csv \
  --time-idx time_idx \
  --target sales \
  --group-ids store,sku \
  --static-categoricals store,sku \
  --time-varying-known-reals time_idx,price,promotion \
  --time-varying-unknown-reals sales \
  --max-encoder-length 36 \
  --max-prediction-length 6
```

The script does not import PyTorch Forecasting; it validates the DataFrame contract and exits nonzero for invalid data.
