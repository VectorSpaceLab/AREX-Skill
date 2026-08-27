# Troubleshooting GluonTS transforms and features

Use this when a transformation chain fails, produces no instances, or yields fields with surprising lengths or shapes.

## Frequency and timestamp problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `AttributeError` or similar around `start.freq` in `AddTimeFeatures` | `start` is a timestamp/string without period frequency metadata. | Build entries through GluonTS dataset helpers with a `freq`, or set `start` to a period-like value that carries the intended frequency. |
| `RuntimeError: Unsupported frequency ...` from `time_features_from_frequency_str` | The frequency is not one of the supported pandas offset families: year, quarter, month, week, day/business day, hour, minute, or second. | Use a pandas-compatible alias in a supported family, e.g. `D`, `H`/`h`, `min`, `W`, `M`/`ME`, or create explicit custom time feature callables. |
| Lags differ after changing frequency alias | The dataset, time-feature, lag, and estimator frequencies are not normalized consistently. | Choose one frequency string at the start of the workflow and reuse it everywhere. |
| Assertion for quarterly lags fails | `get_lags_for_frequency` only supports quarterly multiple `1`. | Use `Q`/`QE` for quarterly, or express multi-quarter spacing as monthly frequencies when that matches the model contract. |

## Feature length and `is_train` problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Time features have only `len(target)` values at prediction time | The chain was called with `is_train=True`, or `pred_length` was set to `0`. | Call the prediction transform with `is_train=False` and set `pred_length=prediction_length` in `AddTimeFeatures`. |
| Time features have `len(target) + prediction_length` values during training | The training transform was called with `is_train=False`. | Call training instance generation with `is_train=True`; future target values should come from the target array, not from extended prediction features. |
| `VstackFeatures` raises a NumPy stacking error | Input feature arrays have different time lengths or incompatible dimensions. | Ensure all stacked fields were created in the same train/prediction mode and have feature-first shape `(features, time)`. Remember that `AddTimeFeatures` with an empty feature list writes `None`; `VstackFeatures` ignores `None` inputs but cannot stack an empty set. |
| Known-future feature is empty after splitting | The feature was length `len(target)` before prediction splitting. | For prediction, generate known-future features with `is_train=False` before `InstanceSplitter`. For externally supplied dynamic features, provide `len(target) + prediction_length` values. |

## Sampler and splitter problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| The chain yields zero instances | `min_past`/`min_future` constraints leave no valid split index, or a stochastic sampler selected none. | Check `len(target) >= min_past + min_future`. For deterministic debugging, use `UniformSplitSampler(p=1.0, ...)`, `TestSplitSampler`, or set `min_instances` on `ExpectedNumInstanceSampler`. |
| `future_target` is empty in prediction mode | This is expected when using `TestSplitSampler`: the target ends at the forecast start. | Do not treat empty prediction `future_target` as failure. Confirm known-future features, not target, have future length `prediction_length`. |
| `future_target` is shorter than `prediction_length` in training | The sampler allowed split indices too close to the end of the target. | Set `min_future=lead_time + future_length` on the training sampler. |
| `past_is_pad` contains leading `1`s | Split index is smaller than `past_length`; left padding was inserted. | If padding is unwanted, set sampler `min_past >= past_length`. If padding is allowed, ensure the model can consume `past_is_pad`. |
| Shape is `(features, time)` when model expects `(time, features)`, or the opposite | `output_NTC` setting on `InstanceSplitter` does not match model input expectations. | Use `output_NTC=True` for time-first split feature tensors; use `False` to preserve feature-first layout. Verify with a one-batch assertion. |
| Original `target` or feature field is missing after splitting | `InstanceSplitter` intentionally deletes each split field and replaces it with `past_...` and `future_...`. | Consume the `past_`/`future_` fields downstream, or keep a copy under a different field before splitting if required. |
| `len(TransformedDataset(...))` is slow or changes results | Length calculation iterates the transformation; stochastic flat-map splitters may resample. | Avoid `len()` for stochastic training transformed datasets. Materialize a bounded iterator only for debugging. |

## Missing-value and dtype problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `np.isnan` raises a type error | Target values are not a numeric floating array. | Use `AsNumpyArray(field=FieldName.TARGET, expected_ndim=..., dtype=np.float32)` or ensure dataset construction produces numeric arrays. |
| NaNs disappeared from `target` | `AddObservedValuesIndicator` imputes by default with `DummyValueImputation(0.0)`. | This is expected. Set `imputation_method=None` if the model or later transform must see NaNs, but keep the observed indicator. |
| Imputed values look non-causal | `MeanValueImputation` uses the mean of all observed values, including future values. | For forecasting features, prefer `DummyValueImputation`, `LastValueImputation`, `CausalMeanValueImputation`, `RollingMeanValueImputation`, or no imputation depending on model requirements. |
| Multivariate target imputation is suspicious | Some imputation strategies are easiest to reason about for one-dimensional targets. | For multivariate targets, first use `imputation_method=None` and verify observed-indicator shape. If imputation is required, test the selected method on the exact `(dim, time)` shape. |
| All-NaN targets turn into zeros | Several imputation methods fall back to dummy zeros when no observed value is available. | Treat all-NaN series as a data-quality issue unless the downstream model explicitly tolerates dummy-imputed series with all-zero observed indicators. |

## Chain composition problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| A later transform cannot find a field | An earlier transform dropped or renamed it, or `VstackFeatures(drop_inputs=True)` removed it. | Order transforms carefully. Use `drop_inputs=False` while debugging, then drop fields once downstream names are stable. |
| Dataset cardinality unexpectedly changes | A `FlatMapTransformation` such as `InstanceSplitter` or a filter is inside the chain. | This is normal for splitters. Place splitters near the end and inspect a small materialized list. |
| Pipeline works before splitting but fails after adding `InstanceSplitter` | A listed `time_series_fields` item is not a time-aligned array or has a shorter future span than required. | Only include fields whose last axis aligns with the target time axis. For prediction, known-future fields need additional future length. |
| Serialization-sensitive pipeline rejects ad hoc functions | `AdhocTransform` and custom lambdas may not be serializable. | Use package transforms or named, importable callables for production model pipelines. Keep ad hoc transforms for temporary experiments only. |

## Quick diagnostic snippet

```python
for entry in list(chain(iter(dataset), is_train=False))[:1]:
    print(sorted(entry))
    for key, value in entry.items():
        if hasattr(value, "shape"):
            print(key, value.shape)
        else:
            print(key, value)
```

Also run the bundled smoke script:

```bash
python scripts/transform_feature_smoke.py
```

Run it from the sub-skill directory or pass the script path from another directory. It imports the installed package only.
