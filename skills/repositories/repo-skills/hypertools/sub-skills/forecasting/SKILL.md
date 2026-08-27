---
name: forecasting
description: "Forecast time series and impute missing values with hyp.predict,
  hyp.impute, and reusable fitted models."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Forecasting

Use this sub-skill for:
- forecasting future rows with `hyp.predict`
- filling missing values with `hyp.impute`
- `hyp.plot(..., predict=..., t=...)` forecast overlays on static plots
- `return_model=True` reuse for fitted forecasters and imputers

Start here:
- [Forecast reference](references/forecast-reference.md)
- [Workflows](references/workflows.md)
- [Troubleshooting](references/troubleshooting.md)
- [Smoke script](scripts/smoke_forecasting.py)

Operational rules:
1. Prefer `hyp.predict(data, model=..., t=..., return_model=...)` for future rows and `hyp.impute(data, model=..., return_model=...)` for missing values.
2. Treat 1-D arrays, flat lists, and `pandas.Series` as univariate `(n, 1)` series. Tuples behave like lists.
3. Reuse fitted objects by passing the returned forecaster/imputer back as `model=` on new data.
4. Keep forecast styling, dashed tails, colors, and legends in `../visualization/`.
5. Keep loading/saving and source data ingestion in `../io/`.
6. Keep generic stage-order questions (`manip`/`normalize`/`reduce`/`align`/`cluster`) in `../pipeline/`.
7. Do not combine `predict=` with `animate=`; forecast overlays are static-only in this release.
8. Treat `Laplace` and `Chronos` as optional add-on models; use base-install models first.

Model families this sub-skill covers:
- Forecasting: `Kalman`, `GaussianProcess`, `AutoRegressor`, `ARIMA`, `Laplace`, `Chronos`
- Imputation: `PPCA`, `SimpleImputer`, `KNNImputer`, `IterativeImputer`, `Kalman`

If the task is really about plotting style or layout, go to `../visualization/`.
If the task is about loading/saving datasets or artifacts, go to `../io/`.
If the task is about the broader pipeline order, go to `../pipeline/`.
