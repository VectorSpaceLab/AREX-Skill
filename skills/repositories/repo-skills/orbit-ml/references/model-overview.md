# Orbit model overview

## Purpose

Use this page when you need the short model-family map before choosing a
subskill.

## Model families

| Family | Constructors | Supported estimators | Best for | Route |
| --- | --- | --- | --- | --- |
| ETS | `ETS(...)` | `stan-map`, `stan-mcmc` | Simple level/seasonality baselines and quick probabilistic forecasts | `forecasting` |
| LGT | `LGT(...)` | `stan-map`, `stan-mcmc`, `pyro-svi` | Local/global trend tasks, LGT-specific regressors, or the Pyro-SVI path | `forecasting` |
| DLT | `DLT(...)` | `stan-map`, `stan-mcmc` | Regressor-rich nowcasting/forecasting and explicit global-trend control | `forecasting` |
| KTRLite | `KTRLite(...)` | `stan-map` | Multi-seasonality with knot control and no exogenous regression | `ktr` |
| KTR | `KTR(...)` | `pyro-svi` | Multi-seasonality with time-varying regression coefficients and knot inspection | `ktr` |

## Shared runtime conventions

- `response_col` defaults to `y`.
- `date_col` defaults to `ds`.
- Model wrappers return forecasters, not bare backend objects.
- `fit()` and `predict()` are the core public workflow methods.
- `get_posterior_samples()`, `get_point_posteriors()`, and `get_training_metrics()` are attached after fit.

## Which subskill to read next

- `forecasting` for ordinary ETS/LGT/DLT forecasting or nowcasting.
- `ktr` for multi-seasonality, knots, or dynamic regression coefficients.
- `evaluation` for backtests, plots, and forecast scoring.
- `utilities` for data preparation, simulation, knots, and EDA helpers.
- `custom-models` for ModelTemplate, forecaster, and estimator internals.
