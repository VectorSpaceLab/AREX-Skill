# API Reference: Orbit KTR / KTRLite

This reference covers the public `orbit.models` wrappers only. Do not instantiate the template classes directly.

## Verified constructors

```python
KTR(
    level_knot_scale=0.1,
    level_segments=10,
    level_knot_distance=None,
    level_knot_dates=None,
    seasonality=None,
    seasonality_fs_order=None,
    seasonality_segments=3,
    seasonal_initial_knot_scale=1.0,
    seasonal_knot_scale=0.1,
    regressor_col=None,
    regressor_sign=None,
    regressor_init_knot_loc=None,
    regressor_init_knot_scale=None,
    regressor_knot_scale=None,
    regression_segments=5,
    regression_knot_distance=None,
    regression_knot_dates=None,
    regression_rho=0.15,
    degree_of_freedom=30,
    date_freq=None,
    coef_prior_list=None,
    flat_multiplier=True,
    residuals_scale_upper=None,
    ktrlite_optim_args=dict(),
    estimator="pyro-svi",
    **kwargs,
)

KTRLite(
    level_knot_scale=0.1,
    level_segments=10,
    level_knot_distance=None,
    level_knot_dates=None,
    seasonality=None,
    seasonality_fs_order=None,
    seasonality_segments=2,
    seasonal_initial_knot_scale=1.0,
    seasonal_knot_scale=0.1,
    degree_of_freedom=30,
    date_freq=None,
    estimator="stan-map",
    suppress_stan_log=True,
    **kwargs,
)
```

## Estimator gate

| Wrapper | Accepted estimator | Default | Notes |
| --- | --- | --- | --- |
| `KTR` | `pyro-svi` | `pyro-svi` | Raises `IllegalArgument` otherwise. Internally fits KTRLite first. |
| `KTRLite` | `stan-map` | `stan-map` | Raises `IllegalArgument` otherwise. |

## Public methods after fit

### KTR

- Forecaster methods: `fit`, `predict`, `fit_wbic`, `get_wbic`, `get_posterior_samples`, `get_point_posteriors`.
- Model-bound inspection methods: `get_regression_coefs`, `get_regression_coef_knots`, `plot_regression_coefs`,
  `get_level_knots`, `get_levels`, `plot_lev_knots`.

Common method signatures:

```python
get_regression_coefs(
    training_meta,
    point_method,
    point_posteriors,
    posterior_samples,
    coefficient_method="smooth",
    date_array=None,
    include_ci=False,
    lower=0.05,
    upper=0.95,
)

get_regression_coef_knots(training_meta, point_method, point_posteriors, posterior_samples)

plot_regression_coefs(
    training_meta,
    point_method,
    point_posteriors,
    posterior_samples,
    coefficient_method="smooth",
    date_array=None,
    include_ci=False,
    lower=0.05,
    upper=0.95,
    with_knot=False,
    is_visible=True,
    ncol=2,
    ylim=None,
    markersize=200,
    figsize=(16, 8),
)
```

Output shapes to remember:

- `get_regression_coefs(include_ci=True)` returns `(mid, lower, upper)` DataFrames.
- `get_regression_coef_knots()` returns a knot table with the date column, `step`, and one column per regressor.
- `get_level_knots()` returns a DataFrame with the training knot dates and `lev_knot`.
- `get_levels()` returns a DataFrame with the training dates and `lev`.
- `plot_regression_coefs(with_knot=True)` overlays knot markers from `get_regression_coef_knots()`.
- `plot_lev_knots()` overlays the response, fitted level curve, and level knots.

### KTRLite

- Forecaster methods: `fit`, `predict`, `get_bic`, `get_posterior_samples`, `get_point_posteriors`.
- Model-bound inspection methods: `get_level_knots`, `get_levels`, `plot_lev_knots`.

Common method signatures:

```python
get_level_knots(training_meta, point_method, point_posteriors, posterior_samples)
get_levels(training_meta, point_method, point_posteriors, posterior_samples)
plot_lev_knots(
    training_meta,
    point_method,
    point_posteriors,
    posterior_samples,
    path=None,
    is_visible=True,
    title="",
    fontsize=16,
    markersize=250,
    figsize=(16, 8),
)
```

## Prediction notes

- `KTR.predict(..., decompose=True)` can return `prediction`, `trend`, `regression`, and seasonal component
  columns such as `seasonality_7` and `seasonality_365.25`.
- `KTRLite.predict(..., decompose=True)` can return `prediction`, `trend`, and seasonal component columns;
  there is no regression component because KTRLite does not fit exogenous regressors.
- KTR full-posterior prediction yields uncertainty columns by default. KTRLite returns point predictions by
  default unless `n_bootstrap_draws > 0` is supplied.
- After fit, the convenience getters are already bound to the fitted forecaster, so routine use is usually
  `model.get_level_knots()` or `model.get_regression_coefs()` with no manual metadata wiring.

## Knot and feature helpers

Use these bundled helpers when you need explicit knot/date conversion or Fourier seasonal columns:

- `orbit.utils.knots.get_knot_idx(...)`
- `orbit.utils.knots.get_knot_dates(start_date, knot_idx, freq)`
- `orbit.utils.features.make_seasonal_regressors(...)`
- `orbit.utils.features.make_fourier_series_df(...)`
