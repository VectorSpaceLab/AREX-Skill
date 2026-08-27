---
name: "forecasting"
description: "Guides PyPOTS forecasting workflows, including future-target data
  keys, forecaster selection, result extraction, evaluation metrics, and HDF5
  lazy-loading."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# PyPOTS Forecasting

Use this sub-skill when the user wants to predict future timesteps from a
partially-observed time-series prefix with PyPOTS.

## Natural Triggers

- "forecast future values with PyPOTS"
- "use BTTF / TEFN / TimeMixer / TimesNet for forecasting"
- "what should `X_pred` contain?"
- "get `predict()[\"forecasting\"]`"
- "evaluate a forecast with MSE or MAE"
- "train a forecaster from HDF5 data"

## First References

- Read [`../../references/data-formats.md#forecasting`](../../references/data-formats.md#forecasting) before building `X` and
  `X_pred`.
- Read [`../../references/api-reference.md`](../../references/api-reference.md) for the `forecast()` helper and
  representative constructor patterns.
- Read [`../../references/model-overview.md#forecasting`](../../references/model-overview.md#forecasting) for model-family choice.
- Read [`../../references/troubleshooting.md`](../../references/troubleshooting.md) when constructor, shape, backend,
  or HDF5 failures appear.
- Use [`../cli/`](../cli/SKILL.md) if the user wants `pypots-cli train`, `predict`, `evaluate`,
  `tune`, or `benchmark` rather than direct Python calls.

## Scope

This route covers:

- Classical/probabilistic forecasting such as `BTTF`.
- Neural forecasting wrappers such as `TEFN`, `TimeMixer`, `TimesNet`,
  `Transformer`, `FITS`, `DLinear`, `CSDI`, `GPT4TS`, `MOMENT`, and `TimeLLM`.
- Future-target data construction with `X_pred`.
- Result extraction through `predict()["forecasting"]` or `forecast()`.
- Regression metrics using `calc_mse`, `calc_mae`, `calc_rmse`, and `calc_mre`.

Route elsewhere:

- Filling missing values in the observed sequence -> [`../imputation/`](../imputation/SKILL.md).
- Class labels -> [`../classification/`](../classification/SKILL.md).
- Anomaly labels -> [`../anomaly-detection/`](../anomaly-detection/SKILL.md).
- Embeddings -> [`../representation/`](../representation/SKILL.md).

## Core Workflow

1. Choose `n_steps` for the observed prefix and `n_pred_steps` for the target
   future window.
2. Build train/validation/test dictionaries with `X` and `X_pred`:

   ```python
   train_set = {"X": train_X[:, :n_steps], "X_pred": train_X[:, n_steps:]}
   val_set = {"X": val_X[:, :n_steps], "X_pred": val_X[:, n_steps:]}
   test_set = {"X": test_X[:, :n_steps], "X_pred": test_X[:, n_steps:]}
   ```

3. Instantiate the model with `n_steps`, `n_features`, `n_pred_steps`, and
   `n_pred_features` when the selected model requires those fields.
4. Train with `model.fit(train_set, val_set)` unless using a model whose
   forecast path is non-neural or differently configured.
5. Predict with `model.predict(test_set)` and read `results["forecasting"]`, or
   call `model.forecast(test_set)`.
6. Evaluate against `X_pred`, masking natural missing positions if needed.

## Minimal Example Shape

```python
from pypots.forecasting import TEFN

model = TEFN(
    n_steps=n_steps,
    n_features=n_features,
    n_pred_steps=n_pred_steps,
    n_pred_features=n_features,
    n_fod=2,
    epochs=1,
    device="cpu",
)
model.fit(train_set, val_set)
forecast = model.forecast(test_set)
```

For `BTTF`, supply matrix-factorization fields such as `rank`, `time_lags`,
`burn_iter`, and `gibbs_iter` rather than the standard neural training knobs.

## Common Decision Points

- Start with `BTTF` or a small neural model on a tiny fixture before running a
  large benchmark.
- Confirm `X_pred` has the same number of samples as `X`.
- Do not use an imputation-only model to predict future steps unless PyPOTS
  exposes a forecasting wrapper for that model.
- LLM/foundation forecasting workflows may need model downloads or extra
  tokenizer packages; choose a non-LLM forecaster if the user has no network or
  cache budget.
- GPU accelerates neural forecasters but is not the default correctness check.

## Validation Signals

A successful forecasting workflow returns `forecasting` with shape compatible
with `X_pred` and finite regression metrics over the intended target positions.
