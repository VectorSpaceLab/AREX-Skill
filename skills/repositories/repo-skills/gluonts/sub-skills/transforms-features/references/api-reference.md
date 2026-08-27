# GluonTS transforms and feature API reference

This reference distills the installed GluonTS transformation and time-feature APIs needed for training and prediction data preparation. It is self-contained; future agents should use the installed package and this skill-owned material rather than reopening the source checkout.

## Field names and shape conventions

Common field constants from `gluonts.dataset.field_names.FieldName`:

| Constant | String value | Purpose |
| --- | --- | --- |
| `FieldName.START` | `"start"` | Period-like start timestamp. Must carry a frequency for time features. |
| `FieldName.TARGET` | `"target"` | Numeric target array. The time axis is the last axis. |
| `FieldName.OBSERVED_VALUES` | `"observed_values"` | Indicator with `1.0` for observed target values and `0.0` for missing values. |
| `FieldName.FEAT_TIME` | `"time_feat"` | Calendar feature matrix, normally `(num_features, time)` before splitting. |
| `FieldName.IS_PAD` | `"is_pad"` | Splitter padding indicator. `past_is_pad` uses `1` where left padding was inserted. |
| `FieldName.FORECAST_START` | `"forecast_start"` | Period where the forecast/future window begins. |

Shape conventions:

- GluonTS transformations assume the time axis is the last axis before splitting.
- A univariate target is usually shape `(T,)`; a multivariate target is usually `(dim, T)`.
- Feature matrices produced by `AddTimeFeatures`, `AddAgeFeature`, and `VstackFeatures` are feature-first before splitting: `(num_features, T)`.
- `InstanceSplitter(output_NTC=True)` transposes split multi-dimensional arrays to time-first layout. A feature matrix becomes `(past_length, num_features)` for `past_<field>` and `(future_length, num_features)` for `future_<field>`. With `output_NTC=False`, split fields remain feature-first.

## Transformation base classes

| API | Contract | Practical use |
| --- | --- | --- |
| `Transformation()` | Abstract base with `__call__(data_it, is_train)` over an iterable of `DataEntry` dictionaries. Supports `.chain(other)`, `+`, and `.apply(dataset, is_train=True)`. | Use only through concrete subclasses. |
| `MapTransformation()` | Yields exactly one transformed entry per input entry by calling `map_transform(data.copy(), is_train)`. | For train/prediction-aware features such as time or age features. |
| `SimpleTransformation()` | A `MapTransformation` whose logic ignores `is_train` and calls `transform(data)`. | For conversion, observed indicators, field renames/removals, stacking. |
| `FlatMapTransformation()` | Yields zero or more entries per input entry by calling `flatmap_transform(data.copy(), is_train)`. | For instance splitters and filters. A chain containing these can change dataset length. |
| `Chain(transformations)` | Applies transformations sequentially. Nested chains are flattened and `Identity` transforms are dropped. | Primary pipeline container for feature engineering and splitting. |
| `TransformedDataset(base_dataset, transformation, is_train=True)` | Lazy dataset wrapper produced by `transformation.apply(...)`. Iteration applies the transform. | Good for passing transformed streams onward. Avoid relying on `len()` for stochastic or flat-map training pipelines because it iterates the transformation. |

The call pattern is always:

```python
transformed_iter = chain(iter(dataset), is_train=True)   # training windows
prediction_iter = chain(iter(dataset), is_train=False)  # prediction windows
```

## Feature and conversion transformations

| API | Signature summary | Output / behavior |
| --- | --- | --- |
| `AsNumpyArray(field, expected_ndim, dtype=np.float32)` | Converts one field to a NumPy array and asserts dimensionality. | Use before transforms that need numeric arrays, especially when input targets came from Python lists or mixed values. |
| `AddObservedValuesIndicator(target_field, output_field, imputation_method=DummyValueImputation(0.0), dtype=np.float32)` | Computes missing-value mask via `np.isnan`. | Adds an indicator matching the target shape. By default, replaces NaNs in `target_field` with `0.0`; set `imputation_method=None` to leave target NaNs while still adding the indicator. |
| `AddTimeFeatures(start_field, target_field, output_field, time_features, pred_length, dtype=np.float32)` | Uses `pd.period_range(start, periods=length, freq=start.freq)` and stacks `feat(index)` results. | If `is_train=True`, output length is `len(target)`. If `is_train=False`, output length is `len(target) + pred_length`. Empty `time_features` writes `None`. |
| `AddAgeFeature(target_field, output_field, pred_length, log_scale=True, dtype=np.float32)` | Adds a monotonic age feature. | Output shape `(1, len(target))` in training and `(1, len(target) + pred_length)` in prediction. |
| `AddConstFeature(output_field, target_field, pred_length, const=1.0, dtype=np.float32)` | Adds a constant dynamic feature. | Same train/prediction length behavior as `AddTimeFeatures`. |
| `VstackFeatures(output_field, input_fields, drop_inputs=True, h_stack=False)` | Stacks non-`None` input fields with `np.vstack` by default or `np.hstack` if `h_stack=True`. | Useful to combine age/time/constant features into one dynamic feature matrix. Drops source fields unless `drop_inputs=False`. |
| `RemoveFields(field_names)`, `RenameFields(mapping)`, `SelectFields(input_fields, allow_missing=False)` | Field management transforms. | Keep final model inputs tidy after feature creation. |

### Missing-value imputation choices

| Imputation class | Behavior | Use notes |
| --- | --- | --- |
| `DummyValueImputation(dummy_value=0.0)` | Replaces every NaN with the dummy value. | Safe deterministic default used by `AddObservedValuesIndicator`. |
| `LeavesMissingValues()` | Leaves NaNs unchanged. | Prefer `imputation_method=None` if you only need an observed indicator and no imputation call. |
| `MeanValueImputation()` | Replaces NaNs by the mean of non-missing values. | Non-causal; can leak future information in training features. |
| `LastValueImputation()` | Forward-fills from the last observed value and backfills leading NaNs. | Common for univariate targets; verify behavior before using on multivariate targets. |
| `CausalMeanValueImputation()` | Uses averages based on values up to each time point. | More appropriate than global mean when avoiding future leakage. |
| `RollingMeanValueImputation(window_size=10)` | Uses a rolling causal mean. | `window_size < 1` is coerced to `1`. |

For multivariate targets, `AddObservedValuesIndicator(..., imputation_method=None)` is often the safest first pass because the observed indicator has the same shape as the target and no one-dimensional imputation assumption is applied.

## Time features

Import from `gluonts.time_feature`:

```python
from gluonts.time_feature import time_features_from_frequency_str, get_lags_for_frequency
```

`time_features_from_frequency_str(freq_str)` returns a list of callables appropriate for a pandas-compatible frequency string:

| Frequency family | Returned normalized feature examples |
| --- | --- |
| Year begin/end | no automatic features |
| Quarter/month | `month_of_year` |
| Week | `day_of_month`, `week_of_year` |
| Day/business day | `day_of_week`, `day_of_month`, `day_of_year` |
| Hour | `hour_of_day`, `day_of_week`, `day_of_month`, `day_of_year` |
| Minute | `minute_of_hour`, `hour_of_day`, `day_of_week`, `day_of_month`, `day_of_year` |
| Second | `second_of_minute`, `minute_of_hour`, `hour_of_day`, `day_of_week`, `day_of_month`, `day_of_year` |

Normalized features return NumPy arrays with values in approximately `[-0.5, 0.5]`. Integer-index variants such as `hour_of_day_index`, `day_of_week_index`, and `month_of_year_index` are available when categorical cardinalities are needed.

`get_lags_for_frequency(freq_str, lag_ub=1200, num_lags=None, num_default_lags=7)` returns lag indices for autoregressive models. The result starts with default lags `[1, ..., num_default_lags]` and then adds seasonal lags derived from the frequency, bounded by `lag_ub` and truncated by `num_lags` when supplied. Quarterly frequencies only support multiple `1`; use monthly multiples for multi-quarter spacing.

## Samplers

All discrete samplers inherit `InstanceSampler(axis=-1, min_past=0, min_future=0)`. For a target array `ts`, the allowed split-index interval is:

```text
a = min_past
b = ts.shape[axis] - min_future
valid sampled index i satisfies a <= i <= b
```

| API | Behavior | Typical use |
| --- | --- | --- |
| `UniformSplitSampler(p, min_past=..., min_future=...)` | Samples each valid index with fixed probability `p`. | Exhaustive training fixtures with `p=1.0` or stochastic training windows. |
| `ExpectedNumInstanceSampler(num_instances, min_instances=0, min_past=..., min_future=...)` | Tracks average window size across calls and adjusts sampling probability to average `num_instances` windows per series. | Default-style training sampler for larger datasets. It is stateful and stochastic. |
| `NumInstanceSampler(N, min_past=..., min_future=...)` | Samples exactly `N` indices uniformly with replacement from the valid interval. | Bounded synthetic checks. |
| `TestSplitSampler(min_past=...)` | Selects the last point as the forecast start and requires the interval to be non-empty. | Prediction/inference transformation. It sets `min_future=0`. |
| `ValidationSplitSampler(min_past=..., min_future=...)` | Prediction-style sampler that allows an empty interval. | Validation flows where short series may appear. |

For training splitters, set `min_future >= lead_time + future_length` so each sampled index has enough target values for `future_target`. For prediction splitters, `future_target` is normally empty because the target ends at the forecast start.

## Instance splitters

### `InstanceSplitter`

Signature summary:

```python
InstanceSplitter(
    target_field,
    is_pad_field,
    start_field,
    forecast_start_field,
    instance_sampler,
    past_length,
    future_length,
    lead_time=0,
    output_NTC=True,
    time_series_fields=[],
    dummy_value=0.0,
)
```

Behavior:

- Removes `target_field` and each `time_series_fields` entry from the output.
- Adds `past_<field>` and `future_<field>` for the target and each listed time-series field.
- Adds `past_<is_pad_field>` with length `past_length` and `1` where left padding was inserted.
- Adds `forecast_start_field = start + sampled_index + lead_time`.
- Pads the left side of the past window with `dummy_value` when the sampled index is smaller than `past_length`.
- Slices future windows from `idx + lead_time` through `idx + lead_time + future_length`.

Training example requirements:

- `is_train=True` on the chain.
- A sampler with `min_future=lead_time + future_length`.
- Target length long enough to produce valid windows, unless incomplete padded contexts are intended.

Prediction example requirements:

- `is_train=False` on the chain.
- A `TestSplitSampler(min_past=context_length)` or validation sampler.
- Known-future dynamic fields, such as time features, must already be length `len(target) + prediction_length`. `AddTimeFeatures(..., pred_length=prediction_length)` supplies that length only when the chain is called with `is_train=False`.

### `CanonicalInstanceSplitter` and `TFTInstanceSplitter`

`CanonicalInstanceSplitter` creates a single `past_<target>` style context window and optionally returns prediction features when `use_prediction_features=True` and `prediction_length` is provided. It is useful for model APIs that expect a fixed `instance_length` instead of separate past/future target windows.

`TFTInstanceSplitter` is specialized for Temporal Fusion Transformer-style inputs. It inherits the basic past/future splitting behavior but keeps known dynamic features as combined past-plus-future tensors and can handle past-only dynamic fields separately. Use it only when the estimator or model input contract specifically asks for TFT-style tensors.
