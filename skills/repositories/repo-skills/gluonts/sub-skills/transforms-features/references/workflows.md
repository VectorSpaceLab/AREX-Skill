# Transformation and feature workflows

Use these recipes after a dataset has already been built as a GluonTS iterable of `DataEntry` dictionaries. The recipes import only the installed `gluonts` package.

## Common imports

```python
import numpy as np

from gluonts.dataset.common import ListDataset
from gluonts.dataset.field_names import FieldName
from gluonts.transform import (
    AddAgeFeature,
    AddObservedValuesIndicator,
    AddTimeFeatures,
    AsNumpyArray,
    Chain,
    ExpectedNumInstanceSampler,
    InstanceSplitter,
    TestSplitSampler,
    VstackFeatures,
)
from gluonts.time_feature import get_lags_for_frequency, time_features_from_frequency_str
```

## Workflow 1: add observed indicators and time features

Use this when you need feature-enriched entries but not sampled windows yet.

```python
freq = "D"
prediction_length = 7

dataset = ListDataset(
    [{"start": "2024-01-01", "target": [1.0, np.nan, 3.0, 4.0]}],
    freq=freq,
)

feature_chain = Chain(
    [
        AsNumpyArray(field=FieldName.TARGET, expected_ndim=1),
        AddObservedValuesIndicator(
            target_field=FieldName.TARGET,
            output_field=FieldName.OBSERVED_VALUES,
        ),
        AddTimeFeatures(
            start_field=FieldName.START,
            target_field=FieldName.TARGET,
            output_field=FieldName.FEAT_TIME,
            time_features=time_features_from_frequency_str(freq),
            pred_length=prediction_length,
        ),
    ]
)

train_entry = next(iter(feature_chain(iter(dataset), is_train=True)))
pred_entry = next(iter(feature_chain(iter(dataset), is_train=False)))

assert train_entry[FieldName.OBSERVED_VALUES].tolist() == [1.0, 0.0, 1.0, 1.0]
assert not np.isnan(train_entry[FieldName.TARGET]).any()  # default dummy imputation
assert train_entry[FieldName.FEAT_TIME].shape[-1] == len(train_entry[FieldName.TARGET])
assert pred_entry[FieldName.FEAT_TIME].shape[-1] == len(pred_entry[FieldName.TARGET]) + prediction_length
```

Notes:

- `AddObservedValuesIndicator` is a simple transform and ignores `is_train`.
- `AddTimeFeatures` uses `is_train` to decide whether to append `prediction_length` future periods.
- If `time_features_from_frequency_str(freq)` returns an empty list, `AddTimeFeatures` writes `None`; either omit it from stacking or supply a different feature such as a constant.

## Workflow 2: create training instances

Use this when an estimator expects sampled context/future windows.

```python
freq = "D"
context_length = 14
prediction_length = 3
lead_time = 0

train_dataset = ListDataset(
    [
        {
            "start": "2024-01-01",
            "target": np.arange(40, dtype=np.float32),
        }
    ],
    freq=freq,
)

train_chain = Chain(
    [
        AsNumpyArray(field=FieldName.TARGET, expected_ndim=1),
        AddObservedValuesIndicator(
            target_field=FieldName.TARGET,
            output_field=FieldName.OBSERVED_VALUES,
        ),
        AddTimeFeatures(
            start_field=FieldName.START,
            target_field=FieldName.TARGET,
            output_field=FieldName.FEAT_TIME,
            time_features=time_features_from_frequency_str(freq),
            pred_length=prediction_length,
        ),
        AddAgeFeature(
            target_field=FieldName.TARGET,
            output_field="age",
            pred_length=prediction_length,
            log_scale=True,
        ),
        VstackFeatures(
            output_field="dynamic_feat",
            input_fields=["age", FieldName.FEAT_TIME],
            drop_inputs=True,
        ),
        InstanceSplitter(
            target_field=FieldName.TARGET,
            is_pad_field=FieldName.IS_PAD,
            start_field=FieldName.START,
            forecast_start_field=FieldName.FORECAST_START,
            instance_sampler=ExpectedNumInstanceSampler(
                num_instances=2.0,
                min_past=context_length,
                min_future=lead_time + prediction_length,
            ),
            past_length=context_length,
            future_length=prediction_length,
            lead_time=lead_time,
            time_series_fields=["dynamic_feat", FieldName.OBSERVED_VALUES],
        ),
    ]
)

instances = list(train_chain(iter(train_dataset), is_train=True))
assert instances
one = instances[0]
assert FieldName.TARGET not in one
assert one[f"past_{FieldName.TARGET}"].shape[0] == context_length
assert one[f"future_{FieldName.TARGET}"].shape[0] == prediction_length
assert one[f"past_{FieldName.IS_PAD}"].shape[0] == context_length
```

Training sampler rules:

- `min_past=context_length` prevents left-padded contexts. Use smaller `min_past` only when padded contexts are desired.
- `min_future=lead_time + prediction_length` is the usual safe setting for target training windows.
- `ExpectedNumInstanceSampler` is stochastic and stateful. For deterministic tests, set `np.random.seed(...)`, use `UniformSplitSampler(p=1.0, ...)`, or use a prediction sampler when one final window is enough.

## Workflow 3: create prediction instances with known future time features

Prediction transformation is similar, but the target normally ends at the forecast start. Future calendar features are still available because `AddTimeFeatures` extends them when `is_train=False`.

```python
freq = "D"
context_length = 14
prediction_length = 3

prediction_dataset = ListDataset(
    [{"start": "2024-02-01", "target": np.arange(25, dtype=np.float32)}],
    freq=freq,
)

prediction_chain = Chain(
    [
        AsNumpyArray(field=FieldName.TARGET, expected_ndim=1),
        AddObservedValuesIndicator(
            target_field=FieldName.TARGET,
            output_field=FieldName.OBSERVED_VALUES,
        ),
        AddTimeFeatures(
            start_field=FieldName.START,
            target_field=FieldName.TARGET,
            output_field=FieldName.FEAT_TIME,
            time_features=time_features_from_frequency_str(freq),
            pred_length=prediction_length,
        ),
        InstanceSplitter(
            target_field=FieldName.TARGET,
            is_pad_field=FieldName.IS_PAD,
            start_field=FieldName.START,
            forecast_start_field=FieldName.FORECAST_START,
            instance_sampler=TestSplitSampler(min_past=context_length),
            past_length=context_length,
            future_length=prediction_length,
            time_series_fields=[FieldName.FEAT_TIME],
        ),
    ]
)

prediction_instance = next(iter(prediction_chain(iter(prediction_dataset), is_train=False)))
assert prediction_instance[f"past_{FieldName.TARGET}"].shape[0] == context_length
assert prediction_instance[f"future_{FieldName.TARGET}"].shape[0] == 0
assert prediction_instance[f"future_{FieldName.FEAT_TIME}"].shape[0] == prediction_length
```

If a model also asks for past observed values at prediction time, include `FieldName.OBSERVED_VALUES` in `time_series_fields` and consume `past_observed_values`. Do not expect future observed values to exist unless you deliberately provide a future-length observed indicator.

## Workflow 4: use `TransformedDataset`

Any transformation can wrap a base dataset lazily:

```python
transformed = feature_chain.apply(dataset, is_train=True)
for entry in transformed:
    assert FieldName.FEAT_TIME in entry
```

Use this for map/simple feature transforms or deterministic prediction splits. Avoid using `len(transformed)` as a cheap size check for stochastic training splitters; computing length iterates the pipeline and may resample instances.

## Workflow 5: choose time features and lags for an estimator

```python
freq = "H"
prediction_length = 24

time_features = time_features_from_frequency_str(freq)
lags_seq = get_lags_for_frequency(freq, num_lags=30)

assert lags_seq[:7] == [1, 2, 3, 4, 5, 6, 7]
```

Use the same `freq` consistently across dataset creation, time features, lag selection, and estimator construction. If the estimator exposes `time_features` or `lags_seq` parameters, pass these objects directly rather than recomputing them with a different alias.

## Output assertion checklist

After transforming a small batch, check:

- `start` has a frequency and `forecast_start` is the expected period.
- `target` was removed by `InstanceSplitter` and replaced by `past_target` and `future_target`.
- `past_target` length equals `context_length`/`past_length`.
- Training `future_target` length equals `prediction_length`; prediction `future_target` may be empty.
- Known-future fields such as time features have future length `prediction_length` in prediction mode.
- `past_is_pad` is all zeros when `min_past >= past_length`; otherwise its leading `1`s correspond to left padding.
- Observed-value indicators have `0.0` exactly where the original target had NaNs.
