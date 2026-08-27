---
name: "imputation"
description: "Guides PyPOTS missing-value imputation workflows, including
  rule-based baselines, neural imputers, data keys, result handling, masks, and
  checkpoint behavior."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# PyPOTS Imputation

Use this sub-skill when the user asks to fill, impute, interpolate, or evaluate
missing values in partially-observed multivariate time series with PyPOTS.

## Natural Triggers

- "impute missing values with PyPOTS"
- "use SAITS / BRITS / MRNN / USGAN"
- "compare Mean, Median, LOCF, and Lerp"
- "get `predict()[\"imputation\"]`"
- "evaluate imputed values with an indicating mask"
- "run imputation from an HDF5 file"

## First References

- Read [`../../references/data-formats.md`](../../references/data-formats.md) before creating `X`, `X_ori`, or HDF5
  files.
- Read [`../../references/api-reference.md`](../../references/api-reference.md) for result keys, helper methods,
  and representative constructor signatures.
- Read [`../../references/model-overview.md#imputation`](../../references/model-overview.md#imputation) for model-family choice.
- Read [`../../references/troubleshooting.md`](../../references/troubleshooting.md) when import, optional dependency,
  shape, key, or checkpoint errors appear.
- Run [`../../scripts/check_install.py`](../../scripts/check_install.py) as a safe import and model-catalog check.

## Scope

This route covers:

- Rule-based imputers: `Mean`, `Median`, `LOCF`, `Lerp`.
- Neural imputers: `SAITS`, `BRITS`, `MRNN`, `USGAN`, `CSAI`, `TEFN`, and
  related backbone-adapted families.
- Imputation result extraction through `predict()["imputation"]` or `impute()`.
- In-memory dict and HDF5 lazy-loading inputs.
- Missingness masks, `X_ori`, artificial missingness, and MSE/MAE evaluation.
- Checkpoint save/load behavior for stateful neural models.

Route elsewhere:

- Future-value prediction -> [`../forecasting/`](../forecasting/SKILL.md).
- Class labels or probabilities -> [`../classification/`](../classification/SKILL.md).
- Anomaly labels -> [`../anomaly-detection/`](../anomaly-detection/SKILL.md).
- CLI-only training or config generation -> [`../cli/`](../cli/SKILL.md).

## Core Workflow

1. Decide whether a no-training baseline is enough.
   - Use `Mean`, `Median`, `LOCF`, or `Lerp` for quick baselines and install
     smoke checks.
   - `LOCF(first_step_imputation=...)` accepts `"zero"`, `"backward"`,
     `"median"`, or `"nan"`-style first-step handling in native tests.
2. Build `test_set = {"X": X_with_nan}` with shape
   `[n_samples, n_steps, n_features]`.
3. For evaluation, also keep `X_ori` and compute an indicating mask over
   artificially hidden values.
4. For neural models, instantiate with architecture dimensions and training
   knobs such as `epochs`, `batch_size`, `optimizer`, `device`, and
   `saving_path`.
5. Call `fit(train_set, val_set)` when the model has a training phase.
6. Call `predict(test_set)` and read `results["imputation"]`; use `impute()`
   when you only need the imputed array.
7. Evaluate with `pypots.nn.functional.calc_mse`, `calc_mae`, `calc_rmse`, or
   `calc_mre` and the appropriate mask.

## Minimal Example Shape

```python
from pypots.imputation import Mean

model = Mean()
results = model.predict({"X": X_with_nan})
imputed = results["imputation"]
```

For a trained neural imputer:

```python
from pypots.imputation import SAITS

model = SAITS(
    n_steps=n_steps,
    n_features=n_features,
    n_layers=1,
    d_model=8,
    n_heads=1,
    d_k=8,
    d_v=8,
    d_ffn=8,
    epochs=1,
    device="cpu",
)
model.fit(train_set, val_set)
imputed = model.impute(test_set)
```

## Common Decision Points

- Use a rule-based imputer before a heavy model to verify data shapes.
- Prefer `device="cpu"` for deterministic smoke checks; switch to CUDA for
  speed only after the API path works.
- Do not assume that two task modules with the same class name accept the same
  constructor arguments.
- If a model requires multiple optimizers (`USGAN`), pass the correct optimizer
  field names instead of a single generic `optimizer`.
- Keep HDF5 input keys identical to the in-memory dict keys.

## Validation Signals

A successful imputation workflow returns an array with the same leading shape as
`X`, contains no unexpected `NaN` values, and computes metrics only on intended
missing positions.
