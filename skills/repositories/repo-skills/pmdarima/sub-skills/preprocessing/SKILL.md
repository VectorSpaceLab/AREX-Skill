---
name: preprocessing
description: "Configure pmdarima target transforms, Fourier and date regressors,
  and ordered Pipeline integration with explicit inverse and exogenous-data
  contracts."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Preprocessing operating skill

Use this route when a pmdarima forecasting workflow needs a Box-Cox/log
endogenous transform, Fourier seasonal regressors, calendar/date regressors, or
`pmdarima.pipeline.Pipeline` composition. Read [workflows](references/workflows.md)
for the decision and composition procedure, [api-reference](references/api-reference.md)
for exact signatures and shapes, and [troubleshooting](references/troubleshooting.md)
before relaxing a validation error or accepting a lossy inverse.

## Fast routing

- Stabilize a positive or shifted target: choose `BoxCoxEndogTransformer` or
  `LogEndogTransformer`; decide the shift and non-positive policy first.
- Represent fixed seasonality as regressors: use `FourierFeaturizer(m, k)`;
  it can synthesize future rows without future `y`.
- Encode known calendar effects: use `DateFeaturizer(column_name=...)` with a
  pandas datetime column; supply future dates explicitly.
- Chain stages: use named preprocessing transformers before a final pmdarima
  `ARIMA`/`AutoARIMA` in `Pipeline`.

## Non-negotiable contracts

1. Endogenous transformers require `y`; exogenous transformers require `X`.
   Fourier is the exception at transform time because its fitted time index can
   generate features. `DateFeaturizer` always needs a DataFrame containing its
   configured datetime column.
2. `fit_transform(y, X)` returns `(y_out, X_out)`, including when `X` was
   omitted. Pass both tuple items to the next stage; target transformers pass
   `X` through and feature transformers pass `y` through.
3. Fit only on training rows. Keep the seasonal period, harmonic count, date
   schema, shifts, and generated feature names fixed between fit and forecast.
4. In a pipeline, intermediate stages must be `BaseTransformer` instances and
   the last stage must be a pmdarima `BaseARIMA` estimator such as `ARIMA` or
   `AutoARIMA`. Pipeline preserves the supplied stage order and, at fit, clones
   each intermediate transformer (the final estimator is the supplied final
   step), records DataFrame feature order, and inverse-transforms endogenous
   predictions in reverse stage order by default.
5. A model fitted with exogenous columns needs compatible future `X`. Fourier
   can make its own future rows; DateFeaturizer cannot invent dates. Inspect
   `pipe.transform(...)` and its columns before calling `predict(...)`.

## Scope boundary

This skill covers transform configuration, tuple/inverse semantics, feature
schema, and pipeline composition. It does not cover ARIMA order search,
temporal cross-validation, or serialization/persistence/update lifecycle.

## Bundled references

- [API reference](references/api-reference.md)
- [Workflows](references/workflows.md)
- [Troubleshooting](references/troubleshooting.md)

Evidence basis: pmdarima source tag `v2.1.1`, focused preprocessing and pipeline
implementation/tests, and the repository's pipeline recipes. Runtime API
smokes used the verified inspection environment; its reported package version
was `0.0.0`, so that environment fact is not treated as the source version.
