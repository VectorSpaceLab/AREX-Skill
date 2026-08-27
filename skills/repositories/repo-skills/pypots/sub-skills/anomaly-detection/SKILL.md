---
name: "anomaly-detection"
description: "Guides PyPOTS anomaly-detection workflows, including detector
  inputs, anomaly-rate configuration, output keys, binary metrics, and
  backend/data pitfalls."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# PyPOTS Anomaly Detection

Use this sub-skill when the user wants PyPOTS to detect anomalous timesteps or
samples in partially-observed time series.

## Natural Triggers

- "detect anomalies with PyPOTS"
- "use TimesNet / TEFN / TimeMixer / Transformer for anomaly detection"
- "what does `anomaly_rate` do?"
- "read `predict()[\"anomaly_detection\"]`"
- "compute accuracy, precision, recall, or F1 for anomaly labels"
- "why are anomaly labels named `anomaly_y` in tests?"

## First References

- Read [`../../references/data-formats.md#anomaly-detection`](../../references/data-formats.md#anomaly-detection) for `X`,
  `anomaly_y`, and CLI label caveats.
- Read [`../../references/api-reference.md`](../../references/api-reference.md) for detector helpers and result
  keys.
- Read [`../../references/model-overview.md#anomaly-detection`](../../references/model-overview.md#anomaly-detection) for model-family
  choice.
- Read [`../../references/troubleshooting.md`](../../references/troubleshooting.md) for data, CUDA, checkpoint, and
  result-key failures.
- Use [`../cli/`](../cli/SKILL.md) for CLI-driven train/predict/evaluate flows.

## Scope

This route covers:

- Detector models such as `TimesNet`, `TEFN`, `TimeMixer`, `Transformer`,
  `FiLM`, `SegRNN`, `ImputeFormer`, `PatchTST`, `DLinear`, `SAITS`,
  `iTransformer`, `Crossformer`, `Pyraformer`, `FEDformer`, `Informer`,
  `ETSformer`, `NonstationaryTransformer`, and `TimeMixerPP`.
- Constructor-time `anomaly_rate` handling.
- Result extraction through `predict()["anomaly_detection"]` or `detect()`.
- Binary classification-style metrics for anomaly labels.
- In-memory dict and HDF5 lazy-loading inputs.

Route elsewhere:

- Missing-value imputation without anomaly labels -> [`../imputation/`](../imputation/SKILL.md).
- Future-value forecasting -> [`../forecasting/`](../forecasting/SKILL.md).
- Sample classification labels -> [`../classification/`](../classification/SKILL.md).
- Embeddings for later detectors -> [`../representation/`](../representation/SKILL.md).

## Core Workflow

1. Prepare `X` with shape `[n_samples, n_steps, n_features]`.
2. Choose an `anomaly_rate` in `(0, 1)` that matches expected anomaly density.
3. Instantiate the detector with `n_steps`, `n_features`, `anomaly_rate`, and
   model-specific architecture fields.
4. Train with `fit(train_set, val_set)` where train/validation dicts contain at
   least `X`; native fixtures also keep `anomaly_y` for metric checks.
5. Predict with `predict(test_set)` and read `results["anomaly_detection"]`, or
   call `detect(test_set)`.
6. Evaluate with `calc_acc` and `calc_precision_recall_f1` when ground-truth
   anomaly labels are available.

## Minimal Example Shape

```python
from pypots.anomaly_detection import TimesNet

model = TimesNet(
    n_steps=n_steps,
    n_features=n_features,
    anomaly_rate=0.05,
    n_layers=1,
    top_k=1,
    d_model=16,
    d_ffn=16,
    n_kernels=3,
    epochs=1,
    device="cpu",
)
model.fit({"X": train_X}, {"X": val_X})
anomalies = model.detect({"X": test_X})
```

If using native test-style labels, keep:

```python
test_anomaly_y = dataset["test_anomaly_y"].flatten()
```

Then compare model outputs to those labels with the metric helpers.

## Common Decision Points

- Use a tiny CPU fixture before a large detector run.
- Verify `0 < anomaly_rate < 1`; the base detector asserts this range.
- Do not reuse a forecasting or imputation config for anomaly detection without
  checking task-specific constructor parameters.
- Make sure the evaluation label key matches the code path. Native tests use
  `anomaly_y`; CLI evaluation currently checks binary targets through `y`.
- If the model emits scores instead of hard labels, confirm the metric helper's
  expected input before interpreting the result.

## Validation Signals

A successful anomaly workflow returns `anomaly_detection` and can compute finite
accuracy/precision/recall/F1 values against the chosen binary label array.
