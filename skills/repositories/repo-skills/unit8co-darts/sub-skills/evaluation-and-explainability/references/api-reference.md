# Evaluation API reference

## Deterministic metric families

Use with actual and deterministic forecast `TimeSeries`:

```python
from darts.metrics import mae, mse, rmse, mape, smape, r2_score

score = rmse(actual, forecast)
```

If the forecast is stochastic, convert to a point summary intentionally, for example median/quantile series, before deterministic metrics.

## Probabilistic metric families

Darts metrics include quantile and interval-style metrics. Names evolve, so inspect the installed `darts.metrics` module when using a less common metric. Important parameter distinction:

- `q`: individual quantile(s), used by quantile metrics such as quantile loss.
- `q_interval`: lower/upper interval tuple(s), used by interval coverage/width metrics such as interval coverage (`ic`) and interval width (`iw`/`iws`).

Example:

```python
from darts.metrics import ic, iw, mql

import numpy as np
coverage = ic(actual, stochastic_forecast, q_interval=(0.05, 0.95), time_reduction=np.nanmean)
width = iw(actual, stochastic_forecast, q_interval=(0.05, 0.95), time_reduction=np.nanmean)
loss_by_quantile = mql(actual, stochastic_forecast, q=[0.1, 0.5, 0.9])
loss = float(np.nanmean(loss_by_quantile))
```

## Reductions and output shape

Many metrics expose reductions along time, component, and series axes:

- `time_reduction`: aggregate over time points.
- `component_reduction`: aggregate over components.
- `series_reduction`: aggregate over a sequence of series.

To keep per-component values while aggregating time, use a time reduction but leave component reduction unset or `None` if supported by the metric. Always inspect the returned type/shape.

## Anomaly/classification boundary

- Continuous anomaly scores: evaluate as score/ranking/regression-like outputs if labels and metric choice support it.
- Binary detector outputs: evaluate as classification labels (precision/recall/F1/accuracy) when binary ground truth exists.

## SHAP explainability

```python
from darts.explainability import ShapExplainer

explainer = ShapExplainer(model, background_series=background)
result = explainer.explain(foreground)
```

Use a fitted, supported model such as a sklearn-like Darts forecasting model. Keep background small and representative. Avoid plotting unless the user requests a file/figure and the environment supports it.
