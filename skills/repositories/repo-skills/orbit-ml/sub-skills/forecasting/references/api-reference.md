# ETS/LGT/DLT Public API Reference

Use these signatures and option names for Orbit `orbit-ml` 1.1.5.1. Import
models from the public package surface:

```python
from orbit.models import ETS, LGT, DLT
```

## Constructor signatures

```python
ETS(
    seasonality=None,
    seasonality_sm_input=None,
    level_sm_input=None,
    estimator="stan-mcmc",
    suppress_stan_log=True,
    **kwargs,
)

LGT(
    seasonality=None,
    seasonality_sm_input=None,
    level_sm_input=None,
    regressor_col=None,
    regressor_sign=None,
    regressor_beta_prior=None,
    regressor_sigma_prior=None,
    regression_penalty="fixed_ridge",
    lasso_scale=0.5,
    auto_ridge_scale=0.5,
    slope_sm_input=None,
    estimator="stan-mcmc",
    suppress_stan_log=True,
    **kwargs,
)

DLT(
    seasonality=None,
    seasonality_sm_input=None,
    level_sm_input=None,
    regressor_col=None,
    regressor_sign=None,
    regressor_beta_prior=None,
    regressor_sigma_prior=None,
    regression_penalty="fixed_ridge",
    lasso_scale=0.5,
    auto_ridge_scale=0.5,
    slope_sm_input=None,
    period=1,
    damped_factor=0.8,
    global_trend_option="linear",
    global_cap=1.0,
    global_floor=0.0,
    global_trend_sigma_prior=None,
    forecast_horizon=1,
    estimator="stan-mcmc",
    suppress_stan_log=True,
    **kwargs,
)
```

Common forecaster kwargs accepted through `**kwargs`:

- `response_col="y"`: response column name in training data.
- `date_col="ds"`: date column name in training and prediction data.
- `n_bootstrap_draws=-1`: bootstrap draw count for intervals from point
  estimates; `None`, `0`, or negative values disable MAP/point bootstrap.
- `prediction_percentiles=None`: `None` means `[5, 95]` plus the always-present
  median/50th percentile; pass `[]` to return only the median/point column.
- Estimator kwargs such as `seed`, `verbose`, `num_warmup`, `num_sample`,
  `chains`, `cores`, `algorithm`, `stan_mcmc_args`, `stan_map_args`,
  `num_steps`, `num_particles`, `learning_rate`, `learning_rate_total_decay`,
  `message`, and `init_scale`.

`suppress_stan_log=True` suppresses the `cmdstanpy` logger in this version. Set
it to `False` when debugging Stan compilation or optimization/sampling output.

## Estimator compatibility

| Model | Supported `estimator` values | Forecaster class behavior |
| --- | --- | --- |
| `ETS` | `"stan-map"`, `"stan-mcmc"` | MAP or full Bayesian Stan forecaster |
| `LGT` | `"stan-map"`, `"stan-mcmc"`, `"pyro-svi"` | MAP, full Bayesian Stan, or SVI forecaster |
| `DLT` | `"stan-map"`, `"stan-mcmc"` | MAP or full Bayesian Stan forecaster |

Invalid estimator strings raise `IllegalArgument` from the model wrapper.

## Fit and predict methods

The returned object is a forecaster. Key methods:

```python
model.fit(df, **kwargs)                          # MAP forecaster
model.fit(df, point_method=None, keep_samples=True,
          sampling_temperature=1.0, **kwargs)    # MCMC/SVI forecasters

model.predict(df, decompose=False,
              store_prediction_array=False,
              seed=None, **kwargs)

model.make_future_df(periods=1)
model.get_posterior_samples(relabel=False, permute=True)
model.get_point_posteriors()
model.get_training_meta()
model.get_prediction_meta()
model.get_training_metrics()
model.get_regressors()
```

For MCMC/SVI fits:

- `point_method=None` keeps full posterior predictive behavior.
- `point_method="mean"` or `"median"` aggregates posterior samples before
  prediction.
- `keep_samples=False` can discard full posterior samples after point-posteriors
  are built; `is_fitted()` still remains true.

## Prediction dataframe contract

Training data must contain `date_col` and `response_col`. Prediction data must
contain `date_col`; it does not need `response_col` for future forecasts. If the
model has regressors, both training and prediction data must contain every
column listed in `regressor_col`.

Date values are converted with `pandas.to_datetime`. They must be ordered and
non-repeating. Uneven gaps emit a warning. Prediction may be:

- in-sample: prediction start equals a training date;
- mixed in-sample/out-of-sample: prediction starts inside training and extends
  beyond training;
- pure future: prediction starts after the training end.

Prediction cannot start before the training start.

## Prediction output columns

The date column is prepended to the returned dataframe. The core prediction
column is named `prediction` for the 50th percentile/median or point estimate.
Other percentiles use suffixes: `prediction_5`, `prediction_95`, etc.

`prediction_percentiles` is sorted and the 50th percentile is always added.
Examples:

- `prediction_percentiles=None` returns default interval columns:
  `prediction_5`, `prediction`, `prediction_95` when interval generation is
  active.
- `prediction_percentiles=[10, 90]` returns `prediction_10`, `prediction`,
  `prediction_90` when interval generation is active.
- `prediction_percentiles=[]` returns only `prediction`.

When `decompose=True`, Orbit returns component columns in the same percentile
style:

| Model | Component columns |
| --- | --- |
| `ETS` | `prediction`, `trend`, `seasonality` |
| `LGT` | `prediction`, `trend`, `seasonality`, `regression` |
| `DLT` | `prediction`, `trend`, `seasonality`, `regression` |

If `store_prediction_array=True`, the forecaster stores raw draws in
`model.prediction_array` when a full/bootstrapped prediction array exists.

## Regressor options

`LGT` and `DLT` share the same regressor interface:

```python
regressor_col=["x1", "x2"]
regressor_sign=["+", "="]              # each entry is '+', '-', or '='
regressor_beta_prior=[0.0, 0.0]          # same length as regressor_col
regressor_sigma_prior=[1.0, 1.0]         # same length as regressor_col
regression_penalty="fixed_ridge"         # 'fixed_ridge', 'lasso', 'auto_ridge'
lasso_scale=0.5
auto_ridge_scale=0.5
```

Sign semantics:

- `"+"`: coefficient constrained to `[0, inf)`.
- `"-"`: coefficient constrained to `(-inf, 0]`.
- `"="`: unconstrained coefficient.

If `regressor_sign`, `regressor_beta_prior`, or `regressor_sigma_prior` is
omitted, defaults are used for every regressor. If supplied, each list must have
exactly the same length as `regressor_col`.

After fitting a regressor model, call:

```python
coef_df = model.get_regression_coefs(lower=0.05, upper=0.95)
```

With posterior samples available, the coefficient dataframe includes lower and
upper coefficient quantiles plus probability columns. With MAP-only point
posteriors, it includes the regressor, sign group, and point coefficient.

## DLT-only global trend options

```python
DLT(global_trend_option="linear")     # default
DLT(global_trend_option="loglinear")
DLT(global_trend_option="logistic", global_cap=..., global_floor=...)
DLT(global_trend_option="flat")
```

`global_cap` must be greater than `global_floor` for logistic global trend.
`period` and `seasonality` set the internal time scaling via the maximum of
`period`, `seasonality`, and `1`.

## Future dataframe helper

After fitting a model with no regressors:

```python
future_df = model.make_future_df(periods=12)
predicted = model.predict(future_df)
```

`make_future_df()` infers frequency from the training dates and returns only the
future date column. Do not use it for regressor models unless you add every
future regressor column yourself before calling `predict()`.
