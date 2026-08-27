# Data Validation and Troubleshooting

Use this guide when `TimeSeriesDataSet` construction, `from_dataset()`/`from_parameters()`, or `to_dataloader()` fails or returns unexpected shapes. The focus is PyTorch Forecasting 1.8.0 v1 data preparation.

## Fast triage

Before changing model code, inspect the DataFrame and one dataloader batch:

```python
required = ["time_idx", "target", "series_id"]
assert set(required).issubset(data.columns)
assert data["time_idx"].dtype.kind in "iu"  # integer/unsigned integer
assert not data.duplicated(["series_id", "time_idx"]).any()
assert data["target"].notna().all()

data = data.sort_values(["series_id", "time_idx"]).reset_index(drop=True)

loader = dataset.to_dataloader(train=False, batch_size=4, num_workers=0)
x, y = next(iter(loader))
print(x.keys())
print(x["encoder_cont"].shape, x["encoder_cat"].shape, x["decoder_cont"].shape)
```

If the input is a CSV, run the bundled validator first:

```bash
python scripts/validate_timeseries_dataframe.py data.csv \
  --time-idx time_idx \
  --target target \
  --group-ids series_id \
  --time-varying-known-reals time_idx \
  --time-varying-unknown-reals target
```

## Symptom-to-recovery table

| Symptom or message | Likely cause | Recovery |
|---|---|---|
| `Timeseries index should be of type integer` | `time_idx` is datetime, float, string, or has missing values. | Convert calendar time to a dense integer column. Keep date as a separate known covariate only if needed. |
| `Time difference between steps has been identified as larger than 1 - set allow_missing_timesteps=True` | At least one group has missing rows in the integer time index. | Fill rows yourself, or set `allow_missing_timesteps=True` and define `constant_fill_strategy` for columns where forward-fill is wrong. |
| `values were found to be NA or infinite` | A declared real feature, target, weight, or encoded value contains `NaN`, `inf`, or cannot be encoded. | Fill real NaNs before construction; drop unusable variables; add missingness indicators; configure `NaNLabelEncoder(add_nan=True)` for categorical columns where actual NaN/unknown categories are expected. |
| `Data type of category ... was found to be numeric` | A column declared categorical contains numeric dtype or a pandas categorical with numeric categories. | Convert to string labels, e.g. `data[col] = data[col].astype(str)` before dataset construction. |
| Unknown category `KeyError` during `from_dataset()` or inference | Validation/inference data contains category values absent from training encoders. | Refit the training dataset with `categorical_encoders={col: NaNLabelEncoder(add_nan=True)}` for columns that can contain unknown values, including group id columns when cold-start groups are expected. |
| Warning that some series/groups are not present in the dataset index | Encoder length, prediction length, lags, or `min_prediction_idx` make those series too short. | Reduce `min_encoder_length`, reduce `min_prediction_length`, reduce lags, add more history, or accept that those groups cannot be predicted. |
| `filters should not remove entries all entries` | No sample remains after length, lag, prediction-index, and predict-mode filters. | Inspect per-group lengths and cutoff; reduce required lengths or provide more data. |
| `target ... should be an unknown continuous variable in the future` | Continuous target was declared as `time_varying_known_reals`. | Move target to `time_varying_unknown_reals`; categorical target goes to `time_varying_unknown_categoricals`. |
| `multiple targets / list of targets requires MultiNormalizer` | `target=[...]` was used with a single normalizer. | Use `MultiNormalizer([...])`, one normalizer per target, or rely on `target_normalizer="auto"` if suitable. |
| `EncoderNormalizer is only allowed if min_encoder_length > 1` | Per-encoder target normalization needs more than one encoder observation. | Set `min_encoder_length >= 2` or use `GroupNormalizer`/`TorchNormalizer`. |
| Batch shapes differ from expectation | Static/time-varying or categorical/real declarations do not match intended features; multi-target returns lists. | Inspect `dataset.reals`, `dataset.flat_categoricals`, `dataset.target_names`, and one batch with `num_workers=0`. |
| `batch_sampler="synchronized"` fails or behaves oddly with gaps | Time-synchronized batching does not support missing timesteps. | Use no synchronized sampler, fill gaps explicitly, or avoid `allow_missing_timesteps=True` for synchronized batches. |

## NaNs and infinities

`allow_missing_timesteps=True` is not a NaN handler. It only handles absent rows in the integer `time_idx` sequence. Actual values in existing rows must be valid after encoding and scaling.

Recommended pattern for real-valued variables:

```python
for col in ["sales", "price", "temperature"]:
    data[f"{col}_was_missing"] = data[col].isna().astype("int8").astype(str)
    data[col] = data[col].replace([float("inf"), float("-inf")], None)
    data[col] = data[col].fillna(data[col].median())
```

Then declare missingness indicators as categorical or real covariates:

```python
TimeSeriesDataSet(
    data,
    time_idx="time_idx",
    target="sales",
    group_ids=["series_id"],
    max_encoder_length=30,
    max_prediction_length=7,
    time_varying_known_reals=["time_idx", "price"],
    time_varying_unknown_reals=["sales", "temperature"],
    time_varying_unknown_categoricals=["sales_was_missing", "temperature_was_missing"],
)
```

For categoricals where unknown or missing values are semantically acceptable:

```python
from pytorch_forecasting.data import NaNLabelEncoder

categorical_encoders = {
    "store": NaNLabelEncoder(add_nan=True),
    "sku": NaNLabelEncoder(add_nan=True),
    "holiday_name": NaNLabelEncoder(add_nan=True),
}
```

If a missing category means a real state such as `"no_holiday"`, it is often better to fill that explicit label than to map it to the generic unknown class.

## Missing timesteps and generated rows

When a group has `time_idx` values with gaps, `TimeSeriesDataSet` can generate missing rows on the fly if `allow_missing_timesteps=True`. Recovery choices:

### Fill rows explicitly before construction

Use this when generated values require domain-specific logic.

```python
full_index = (
    data.groupby(["store", "sku"])["time_idx"]
    .agg(["min", "max"])
    .reset_index()
)
# Build each group's complete integer range, merge, then fill columns explicitly.
```

### Let the dataset fill missing rows

Use this when forward filling is acceptable except for a few columns:

```python
dataset = TimeSeriesDataSet(
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

Use `constant_fill_strategy` for columns where a generated row should receive a constant. For example, absent sales rows might mean demand `0.0`; absent sensor readings rarely mean `0.0` and should be filled intentionally.

## Short series and length filters

A sample needs at least `min_encoder_length + min_prediction_length` time steps after accounting for lags and `min_prediction_idx`. Predict mode also chooses one longest sample per group. If groups disappear:

1. Compute per-group counts and time spans after the train/validation cutoff.
2. Check `max_lag`; lagged variables cut off the first `max_lag` rows per group.
3. Lower `min_encoder_length` if short histories are acceptable.
4. Lower `min_prediction_length` only if shorter decoder labels are meaningful.
5. Ensure `min_prediction_idx` does not start after a group's last viable decoder window.

Quick diagnostic:

```python
lengths = data.groupby(["store", "sku"])["time_idx"].agg(["min", "max", "count"])
lengths["span"] = lengths["max"] - lengths["min"] + 1
print(lengths.sort_values("count").head(20))
```

If a group is too short only for validation/test, you can still train on it; it simply will not produce validation/prediction windows for that cutoff.

## Covariate declaration mistakes

### Target declared as known future

The target is unknown at prediction time and should not be in `time_varying_known_reals` or `time_varying_known_categoricals`. Use:

```python
time_varying_unknown_reals=["sales"]
# or for categorical target:
time_varying_unknown_categoricals=["state"]
```

### Same feature declared in multiple covariate roles

Do not declare the same non-target covariate as both static and time-varying, or as both real and categorical. Decide what the model should see:

- If it changes over time, use one of the `time_varying_*` roles.
- If it is constant within a group, use one static role.
- If it is categorical, use a categorical role and string/categorical dtype.
- If it is numeric and ordered/continuous, use a real role.

Group id columns are a special case: they may also be useful static categoricals.

### Known future covariates missing on inference rows

For `predict=True`, future decoder rows must include planned/known features such as price, promotions, and calendar variables. If those columns are missing or NaN in the future horizon, the prediction dataset may fail or produce meaningless decoder inputs.

Recovery:

```python
future = make_future_rows(groups, next_time_idx, horizon)
future["promotion"] = planned_promotion_values
future["price"] = planned_price_values
future["target"] = 0.0  # placeholder only if target is ignored on decoder side for prediction
inference_df = pd.concat([history, future], ignore_index=True)
predict_ds = TimeSeriesDataSet.from_dataset(training, inference_df, predict=True, stop_randomization=True)
```

## Target normalizer issues

### Learning rate finder or training diverges

Use a target normalizer for real-valued targets. Good first choices:

```python
GroupNormalizer(groups=["series_id"], transformation="log1p")
# or
EncoderNormalizer(transformation="relu")
```

For negative targets, avoid log-style transformations. For highly intermittent non-negative targets, check whether `log1p`, `relu`, or `softplus` better matches the output constraints and loss.

### New groups with group normalizer

`GroupNormalizer(groups=[...])` estimates scales per fitted group. Cold-start groups may not have meaningful per-group scales unless the encoder/normalizer can fall back appropriately. If cold-start groups are important, test prediction on synthetic new groups and consider less granular normalization, robust preprocessing, or explicit group-level features.

### Multi-target shape and normalizer mismatch

For `target=["y1", "y2"]`, outputs and `target_scale` can be lists. Use `MultiNormalizer`:

```python
target_normalizer=MultiNormalizer([
    GroupNormalizer(groups=["series_id"]),
    TorchNormalizer(method="identity"),
])
```

Downstream code should handle list targets rather than assuming a single tensor.

## Dataloader shape surprises

If `x["encoder_cont"].shape[-1]` or `x["encoder_cat"].shape[-1]` is unexpected, inspect the dataset's resolved feature lists:

```python
print("reals", dataset.reals)
print("categoricals", dataset.flat_categoricals)
print("targets", dataset.target_names)
print("static_reals", dataset.static_reals)
print("static_categoricals", dataset.static_categoricals)
```

Remember:

- `add_relative_time_idx=True` adds `relative_time_idx` to known reals.
- `add_encoder_length=True` or `"auto"` can add `encoder_length` to static reals when encoder lengths vary.
- `add_target_scales=True` adds `<target>_center` and `<target>_scale` for continuous targets.
- `lags={...}` adds generated lag names such as `<name>_lagged_by_<lag>`.
- Variable groups can flatten multiple underlying columns into categorical inputs.

## Safe debugging sequence

1. Run the bundled CSV validator if starting from a file.
2. Build the smallest realistic DataFrame slice with two groups and enough time steps.
3. Construct `TimeSeriesDataSet` with `target_normalizer=None`, no lags, no variable groups, and `randomize_length=False` to isolate schema issues.
4. Add encoders/normalizers, then lags, then missing-timestep behavior one at a time.
5. Iterate one dataloader batch with `num_workers=0`.
6. Only after the dataset is stable, route model/training choices to the forecasting-models and metrics/tuning sub-skills.
