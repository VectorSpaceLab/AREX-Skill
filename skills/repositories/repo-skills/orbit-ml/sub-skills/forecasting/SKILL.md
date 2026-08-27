---
name: forecasting
description: "Use Orbit ETS, LGT, and DLT for fit/predict forecasting workflows,
  estimator choice, regressors, intervals, decomposition, future frames, and
  missing-response handling."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Forecasting

Use this sub-skill when a task asks for built-in exponential-smoothing-style
forecasting with `ETS`, `LGT`, or `DLT`.

## Read this when

- The user asks to fit, predict, forecast, or nowcast a time-series model with
  `ETS`, `LGT`, or `DLT`.
- The task mentions `stan-map`, `stan-mcmc`, `pyro-svi`, MAP, MCMC, SVI, Pyro,
  posterior samples, point estimates, or bootstrap intervals for these models.
- The task includes exogenous regressors, sign-constrained regression
  coefficients, regression priors, or regression penalties.
- The user needs prediction percentiles, prediction intervals, decomposition,
  regression coefficients, missing-response behavior, or future prediction
  frames.

## What this sub-skill owns

- Model-family comparison for `ETS`, `LGT`, and `DLT`.
- Fit/predict workflows through `from orbit.models import ETS, LGT, DLT`.
- Estimator selection and estimator-specific runtime arguments for MAP, MCMC,
  and LGT Pyro-SVI.
- Prediction percentiles, bootstrapping, posterior/point prediction behavior,
  `decompose=True`, and `store_prediction_array=True`.
- Regressors for `LGT` and `DLT`, including `regressor_col`, `regressor_sign`,
  `regressor_beta_prior`, `regressor_sigma_prior`, `regression_penalty`,
  `lasso_scale`, and `auto_ridge_scale`.
- Missing response handling for ETS/LGT/DLT training data.
- Future dataframe creation with `make_future_df()` when no regressors are
  required.

## What this sub-skill does not own

- KTR or KTRLite workflows: route to `ktr`.
- Backtesting, metrics, forecast plots, diagnostics, BIC/WBIC, or residual
  analysis beyond the model outputs needed here: route to `evaluation`.
- Dataset loaders, simulation helpers, feature utilities, tuning helpers, or
  generic dataframe cleaning: route to `utilities`.
- Custom model templates, forecaster subclasses, Stan/Pyro model internals, or
  new estimator development: route to `custom-models`.

## Start here

1. Choose the model and backend from `references/model-selection.md`.
2. Check exact public signatures and output columns in
   `references/api-reference.md`.
3. Use the recipes in `references/workflow-recipes.md` for fit/predict,
   nowcasting with regressors, intervals, decomposition, missing responses, and
   future frames.
4. If an environment or data issue appears, use `references/troubleshooting.md`.
5. Run `python scripts/smoke_forecasting.py` after installing `orbit-ml` to
   verify a tiny offline ETS MAP and LGT Pyro-SVI fit/predict path. Use
   `--skip-pyro` or `--skip-stan` only when deliberately narrowing the backend
   check.

## Fast routing cheatsheet

- Simple univariate trend/seasonality baseline: start with `ETS`; use
  `estimator="stan-map"` for speed or `"stan-mcmc"` for full Bayesian
  intervals.
- Need LGT behavior or the Pyro-SVI backend: use `LGT`; keep responses
  non-negative.
- Need exogenous regressors, global trend shape control, or new regression work:
  prefer `DLT`; it owns `global_trend_option`, `damped_factor`, and regression
  penalties.
- Need known future covariates for a forecast/nowcast: build the prediction
  dataframe manually with the same regressor columns; do not rely on
  `make_future_df()` for regressor models.
- Need intervals from MAP or point-estimated MCMC/SVI: set
  `n_bootstrap_draws > 0` and pass `prediction_percentiles` as needed.
- Need component output: call `predict(..., decompose=True)` and validate the
  returned component columns before plotting or scoring.

## Good entry points

- `from orbit.models import ETS, LGT, DLT`
- Constructor kwargs: `response_col`, `date_col`, `seasonality`, estimator and
  model-specific options.
- `fit(df, point_method=None, keep_samples=True, sampling_temperature=1.0)` for
  MCMC/SVI forecasters; MAP accepts `fit(df)`.
- `predict(df, decompose=False, store_prediction_array=False, seed=None)`.
- `make_future_df(periods=...)` after fitting a no-regressor model.
- `get_posterior_samples()`, `get_point_posteriors()`, `get_training_meta()`,
  `get_prediction_meta()`, `get_regressors()`, and `get_regression_coefs()`
  when available on regressor models.
