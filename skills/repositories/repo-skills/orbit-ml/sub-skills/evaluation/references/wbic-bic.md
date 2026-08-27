# WBIC / BIC

## Purpose

Use this file when the task is to compare fitted Orbit models with WBIC or BIC rather than forecast error metrics.

## Important distinction

- `orbit.diagnostics.metrics.wbic()` is **not** the implementation to use; it is only a stub.
- The working path is model-level: `fit_wbic()`, `get_wbic()`, and `get_bic()` on fitted model objects.

## WBIC flow

Use WBIC when the estimator path supports the temperature-based fit used by Orbit's Bayesian forecasters.

### Pattern

```python
wbic_value = model.fit_wbic(df=train_df)
print(wbic_value)
print(model.get_wbic())
```

### Notes

- `fit_wbic(df)` refits with sampling temperature set to `log(n)`.
- `get_wbic()` checks that the fitted sampling temperature is compatible before returning the value.
- If the sampling temperature does not match the WBIC requirement, the model raises an error instead of silently returning a number.

### Evidenced model families

The repo examples and tests demonstrate WBIC on these supported paths:

- DLT with `stan-mcmc`
- LGT with `stan-mcmc`
- LGT with `pyro-svi`
- KTR with `pyro-svi`
- ETS in the notebook example

## BIC flow

Use BIC for MAP-style fits.

### Pattern

```python
model.fit(df=train_df)
bic_value = model.get_bic()
print(bic_value)
```

### Notes

- BIC is computed from the fitted training metrics and parameter count.
- The notebook example uses DLT.
- The tests exercise DLT, LGT, and KTRLite MAP paths.

## Practical guidance

- Prefer WBIC for full Bayesian or SVI paths.
- Prefer BIC for MAP paths.
- If you only have forecast predictions, WBIC/BIC is not the right tool; use backtest scoring instead.
- When comparing many models, keep the criterion and estimator family consistent across the comparison set.
