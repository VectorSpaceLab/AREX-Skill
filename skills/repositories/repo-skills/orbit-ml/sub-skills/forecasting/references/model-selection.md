# Forecasting Model and Estimator Selection

This reference covers the public `ETS`, `LGT`, and `DLT` model families in
`orbit.models`.

## Model-family decision guide

| Need | Prefer | Why | Watch for |
| --- | --- | --- | --- |
| Simple univariate baseline with level and optional seasonality | `ETS` | Smallest public model surface: `seasonality`, seasonality smoothing, level smoothing | No regressors; no DLT global trend controls |
| Local/global trend behavior or Pyro-SVI backend | `LGT` | Supports `stan-map`, `stan-mcmc`, and `pyro-svi`; exposes trend, seasonality, and optional regression decomposition | Response values must be non-negative; LGT regression emits a deprecation warning in this version, so prefer DLT for new regressor-heavy work |
| Exogenous regressors, nowcasting with known future covariates, or global trend shape control | `DLT` | Adds damped local trend, `global_trend_option`, logistic bounds, `forecast_horizon`, and regression penalty controls | Stan-only (`stan-map`/`stan-mcmc`); future frames with regressors must be built manually |

### ETS

Use `ETS` for a quick probabilistic exponential-smoothing model when the target
series itself carries enough information. It supports:

- `seasonality`: set to a period length such as `7`, `12`, or `52`; use `None`
  or `1` for non-seasonal fits.
- `seasonality_sm_input`: fixed seasonal smoothing in `[0, 1]`; `None` lets the
  model estimate it.
- `level_sm_input`: fixed level smoothing in `[0, 1]`; `None` lets the model
  estimate it.
- Estimators: `"stan-map"`, `"stan-mcmc"`.

### LGT

Use `LGT` when the task specifically asks for Local Global Trend, needs the
`pyro-svi` backend, or needs legacy LGT regression behavior. It supports the
ETS options plus:

- `slope_sm_input`: fixed slope smoothing in `[0, 1]`; `None` estimates it.
- `regressor_col`, `regressor_sign`, `regressor_beta_prior`,
  `regressor_sigma_prior`.
- `regression_penalty`, `lasso_scale`, `auto_ridge_scale`.
- Estimators: `"stan-map"`, `"stan-mcmc"`, `"pyro-svi"`.

LGT rejects negative response values during fit. Missing responses are allowed
except at the first observation, but non-missing responses must be non-negative.

### DLT

Use `DLT` for most production-style regressor workflows and for explicit global
trend control. It supports the ETS and LGT regression options plus:

- `period`: used with `seasonality` to set the time scaling.
- `damped_factor`: dampens local trend forecasts; smaller values damp more.
- `global_trend_option`: one of `"linear"`, `"loglinear"`, `"logistic"`, or
  `"flat"`.
- `global_cap` and `global_floor`: only meaningful for logistic global trend;
  cap must be greater than floor.
- `global_trend_sigma_prior`: defaults to response standard deviation.
- `forecast_horizon`: optimization forecast horizon for DLT.
- Estimators: `"stan-map"`, `"stan-mcmc"`.

## Estimator decision guide

| Estimator | Models | Use when | Interval behavior |
| --- | --- | --- | --- |
| `"stan-map"` | ETS, LGT, DLT | Need faster point estimates; small smoke tests; deterministic-ish workflows | No intervals unless `n_bootstrap_draws > 0` and more than one prediction percentile is requested |
| `"stan-mcmc"` | ETS, LGT, DLT | Need full Bayesian posterior samples and robust uncertainty | Full posterior predictive percentiles by default; `fit(point_method="mean"|"median")` collapses to point prediction unless bootstrapping is enabled |
| `"pyro-svi"` | LGT only | Need stochastic variational inference or cannot use Stan for LGT | SVI returns approximate posterior samples by default; `fit(point_method="mean"|"median")` collapses to point prediction unless bootstrapping is enabled |

## Practical defaults

- Start with `estimator="stan-map"`, `seasonality=1`, and `verbose=False` for
  tiny local checks.
- For real uncertainty estimates, prefer `estimator="stan-mcmc"` with adequate
  `num_warmup`, `num_sample`, `chains`, and `cores`.
- For fast MCMC experiments, keep `chains=1` and `cores=1`; increase only after
  the data and options are validated.
- For Pyro-SVI, tune `num_steps`, `num_sample`, `num_particles`,
  `learning_rate`, and `init_scale`; more steps/samples improve approximation
  at higher cost.
- Use `seed=...` at construction and `predict(..., seed=...)` when comparing
  repeated runs that include bootstrap or posterior sampling noise.

## Regressor model selection

- For new nowcasting/forecasting tasks with exogenous variables, prefer `DLT`.
- Use `LGT` with regressors only for tasks that explicitly require LGT or Pyro.
- Future prediction data must contain all regressor columns with finite values;
  Orbit cannot invent future covariates.
- `make_future_df()` is only safe for no-regressor models because it creates
  only the future date column.
