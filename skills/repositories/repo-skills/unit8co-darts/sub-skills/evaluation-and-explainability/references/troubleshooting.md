# Evaluation and explainability troubleshooting

## Metric returns unexpected shape or type

Check reduction arguments. A scalar means time/component/series axes were likely all reduced. To keep per-component output, leave component reduction unset when the metric supports it and inspect the returned array/series.

## Metric rejects stochastic or deterministic inputs

- Deterministic point metrics expect deterministic forecasts; convert stochastic forecasts to median/mean/quantile series if appropriate.
- Probabilistic metrics need stochastic forecasts or forecast distributions/samples.

## `q` vs `q_interval` error

Use `q` for individual quantile metrics such as quantile loss. Use `q_interval` as a tuple such as `(0.05, 0.95)` for interval coverage and interval width metrics. Do not pass `[0.05, 0.95]` as `q` to interval metrics unless the installed API explicitly says so.

## Actual and forecast time ranges do not align

Slice or intersect intentionally:

```python
actual_eval = actual.slice_intersect(forecast)
forecast_eval = forecast.slice_intersect(actual)
```

Then assert equal lengths/components before scoring.

## SHAP background complaints or slow explanations

Likely causes:

- background data too large;
- unsupported/unfitted model;
- missing dependencies;
- foreground not shaped like training data.

Fix by using a small representative background, verifying model support, and explaining a tiny foreground first.

## Plotting hangs or fails in headless sessions

Use non-interactive backends, save to an explicit path, or skip plotting. Avoid `plt.show()` in agent checks.
