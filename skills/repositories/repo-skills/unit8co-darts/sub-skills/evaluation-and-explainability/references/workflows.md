# Evaluation and explainability workflows

## Deterministic point forecast metrics

```python
from darts.metrics import mae, rmse

point = forecast.quantile(0.5) if forecast.is_stochastic else forecast
print("MAE", float(mae(actual, point)))
print("RMSE", float(rmse(actual, point)))
```

Validate that `actual` and `point` have matching time ranges/components, or slice/intersect intentionally before scoring.

## Probabilistic intervals and quantile loss

```python
import numpy as np
from darts.metrics import ic, iw, mql

coverage = ic(actual, stochastic_forecast, q_interval=(0.05, 0.95), time_reduction=np.nanmean)
width = iw(actual, stochastic_forecast, q_interval=(0.05, 0.95), time_reduction=np.nanmean)
quantile_loss_by_q = mql(actual, stochastic_forecast, q=[0.1, 0.5, 0.9])
quantile_loss = float(np.nanmean(quantile_loss_by_q))
```

Use `q_interval` for interval coverage/width metrics. Use `q` for individual quantile metrics. Multiple quantiles can return arrays; reduce them deliberately for scalar reports.

## Keep per-component values

When supported by the metric, aggregate time but preserve components:

```python
import numpy as np
from darts.metrics import ae

per_component = ae(actual, forecast, time_reduction=np.nanmean, component_reduction=None)
print(per_component)
```

If a metric returns a scalar by default, explicitly set reductions or use an elementwise/absolute-error metric variant appropriate for the report.

## Backtest output reporting

Historical forecasts may return a sequence of forecasts. Choose whether the report should reduce over:

- forecast horizon time points;
- components;
- multiple series/entities;
- multiple historical forecast origins.

State the reduction choices in the final result.

## SHAP explainability workflow

1. Fit a supported Darts forecasting model, usually a sklearn-like/global model for SHAP.
2. Choose a small background series or list of series representative of training data.
3. Choose foreground examples to explain.
4. Construct `ShapExplainer` only after import/support checks.
5. Avoid plotting by default; return values/tables or save a figure only when requested.

## Headless plotting boundary

In automated agents, prefer:

```python
import matplotlib
matplotlib.use("Agg")
```

Save plots to an explicit user-approved path. Do not call `plt.show()` in headless verification.
