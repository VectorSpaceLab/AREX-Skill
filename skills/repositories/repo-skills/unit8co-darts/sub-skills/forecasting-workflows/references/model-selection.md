# Forecasting model selection

## Fast selection rules

1. **Always create a baseline.** Use `NaiveSeasonal` for obvious seasonality, `NaiveDrift` for trend, or `NaiveMean` for a simple constant baseline.
2. **Respect dependency constraints.** If the user says no torch, do not choose neural models. If `darts[notorch]` extras are missing, avoid Prophet/GBM/StatsForecast families unless the user approves installation.
3. **Match covariate needs.** Many local/statistical models ignore or reject covariates. Use regression/global or torch models for rich covariate support.
4. **Validate before optimizing.** Assert forecast length/start/end, sample count for stochastic forecasts, and metric finiteness before backtesting or hyperparameter search.

## Common model families

| Need | Models to consider | Install boundary | Notes |
| --- | --- | --- | --- |
| Seasonal baseline | `NaiveSeasonal(K=season_length)` | base | No covariates; great sanity check. |
| Trend baseline | `NaiveDrift` | base | No covariates; simple trend extrapolation. |
| Classical probabilistic local model | `ExponentialSmoothing` | base | Supports `num_samples` for stochastic forecasts in common setups. |
| Lagged regression with covariates | `LinearRegressionModel`, `RegressionModel`, `RandomForest` | base for sklearn-backed models | Configure `lags`, `lags_past_covariates`, `lags_future_covariates`. |
| GBM-style regression | `LightGBMModel`, `XGBModel`, `CatBoostModel` | `darts[notorch]` | Optional packages; route install first if missing. |
| Prophet or StatsForecast | `Prophet`, StatsForecast-backed models | `darts[notorch]` | Optional dependencies, model-specific constraints. |
| Neural/global forecasting | `TCNModel`, `NBEATSModel`, `TFTModel`, etc. | `darts[torch]` | Route to `torch-and-foundation-models`. |

## Covariate support troubleshooting

If a user tries:

```python
NaiveSeasonal(K=7).fit(series, past_covariates=past_cov)
```

explain that the model family does not support that argument. Switch to a covariate-capable model such as:

```python
from darts.models import LinearRegressionModel

model = LinearRegressionModel(
    lags=14,
    lags_past_covariates=7,
    lags_future_covariates=[0, 1, 2, 3, 4, 5, 6],
)
```

Then validate covariate spans in `data-processing-and-covariates` before fitting.

## Probabilistic selection

- `num_samples` only has meaning for models that support probabilistic sampling or configured likelihoods.
- For deterministic-only models, either use point metrics or choose a probabilistic-capable model/wrapper.
- Route quantile/interval coverage and `q` vs `q_interval` details to `evaluation-and-explainability`.

## Optional-heavy workflows

Do not install `darts[all]` just because a model is unfamiliar. Install the smallest extra needed by the chosen model family and record unverified optional capabilities when they are outside the task.
