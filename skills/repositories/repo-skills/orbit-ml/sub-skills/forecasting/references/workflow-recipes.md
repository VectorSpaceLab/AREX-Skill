# Forecasting Workflow Recipes

These recipes use only public Orbit APIs and ordinary pandas dataframes.

## 1. Validate the input dataframe first

Before constructing a model, check:

```python
assert date_col in df.columns
assert response_col in df.columns
assert pd.Series(pd.to_datetime(df[date_col])).is_monotonic_increasing
assert not pd.to_datetime(df[date_col]).duplicated().any()
assert pd.notna(df[response_col].iloc[0])  # first response cannot be missing
```

For `LGT`, also ensure all non-missing response values are non-negative. For
`LGT`/`DLT` regressors, confirm every regressor column exists and is finite in
both training and prediction data.

## 2. Minimal ETS fit/predict

Use MAP for fast iteration:

```python
from orbit.models import ETS

ets = ETS(
    response_col="y",
    date_col="ds",
    seasonality=7,
    estimator="stan-map",
    n_bootstrap_draws=500,
    prediction_percentiles=[10, 90],
    seed=2024,
    verbose=False,
)
ets.fit(train_df)
future_df = ets.make_future_df(periods=14)
predicted = ets.predict(future_df, seed=2024)
```

Use MCMC when posterior uncertainty is important:

```python
ets = ETS(
    response_col="y",
    date_col="ds",
    seasonality=7,
    estimator="stan-mcmc",
    num_warmup=500,
    num_sample=500,
    chains=4,
    cores=4,
    stan_mcmc_args={"show_progress": False},
    seed=2024,
    verbose=False,
)
ets.fit(train_df)
predicted = ets.predict(test_or_future_df)
posteriors = ets.get_posterior_samples()
```

## 3. MCMC/SVI point estimates

When using `stan-mcmc` or `pyro-svi`, pass `point_method` to `fit()` when the
user wants a point forecast derived from posterior samples:

```python
model.fit(train_df, point_method="median")  # or "mean"
predicted = model.predict(test_df)
points = model.get_point_posteriors()
```

To add intervals around those point estimates, also set
`n_bootstrap_draws > 0` on the constructor and request at least two prediction
percentiles.

## 4. Prediction intervals and percentile columns

```python
model = ETS(
    response_col="y",
    date_col="ds",
    estimator="stan-map",
    prediction_percentiles=[5, 25, 75, 95],
    n_bootstrap_draws=1000,
)
model.fit(train_df)
pred = model.predict(future_df)
```

Expected prediction columns are date first, then sorted percentiles with median
as the unsuffixed column:

```text
ds, prediction_5, prediction_25, prediction, prediction_75, prediction_95
```

To suppress interval columns, use `prediction_percentiles=[]`. For MAP and
point-estimated MCMC/SVI, non-positive `n_bootstrap_draws` also suppresses
bootstrap intervals.

## 5. Decomposition output

Use `decompose=True` to expose components for downstream plotting or analysis:

```python
pred = model.predict(test_or_future_df, decompose=True)
```

Component families:

- `ETS`: `prediction`, `trend`, `seasonality`.
- `LGT`/`DLT`: `prediction`, `trend`, `seasonality`, `regression`.

With interval generation active, component columns also receive percentile
suffixes, such as `trend_5`, `trend`, `trend_95`.

## 6. DLT nowcast/forecast with known regressors

Use DLT for new regressor workflows. Build the future/nowcast frame manually
because Orbit cannot infer future covariates:

```python
from orbit.models import DLT

regressors = ["promo", "holiday", "price_index"]

dlt = DLT(
    response_col="sales",
    date_col="date",
    seasonality=7,
    estimator="stan-mcmc",
    regressor_col=regressors,
    regressor_sign=["+", "+", "-"],
    regressor_beta_prior=[0.0, 0.0, 0.0],
    regressor_sigma_prior=[1.0, 1.0, 0.5],
    regression_penalty="fixed_ridge",
    num_warmup=500,
    num_sample=500,
    stan_mcmc_args={"show_progress": False},
    seed=2024,
    verbose=False,
)
dlt.fit(train_df)

future_df = pd.DataFrame({
    "date": pd.date_range(train_df["date"].iloc[-1], periods=15, freq="D")[1:],
    "promo": future_promo_values,
    "holiday": future_holiday_flags,
    "price_index": future_price_index,
})
pred = dlt.predict(future_df, decompose=True)
coef_df = dlt.get_regression_coefs(lower=0.05, upper=0.95)
```

If the prediction dataframe starts inside the training range, Orbit treats it as
in-sample or mixed in-sample/future prediction. This is useful for nowcasting
when recent responses are unavailable but regressors are known.

## 7. DLT global trend choices

Switch `global_trend_option` when the global trend shape matters:

```python
DLT(global_trend_option="linear")
DLT(global_trend_option="loglinear")
DLT(global_trend_option="flat")
DLT(global_trend_option="logistic", global_floor=0.0, global_cap=100.0)
```

For logistic trend, validate `global_cap > global_floor`. Use `damped_factor` to
control local-trend carryover; smaller values damp local trend more strongly.

## 8. Regression penalties

Use the exact option names:

```python
DLT(regression_penalty="fixed_ridge")
DLT(regression_penalty="auto_ridge", auto_ridge_scale=0.5)
DLT(regression_penalty="lasso", lasso_scale=0.5)
```

- `fixed_ridge`: fixed normal prior scale from `regressor_sigma_prior`.
- `auto_ridge`: learns/adapts coefficient scales; useful when prior scales are
  uncertain.
- `lasso`: stronger shrinkage for sparse/high-dimensional regressors.

For high-dimensional regression, examples use fixed small smoothing parameters
such as `level_sm_input=0.01` and `slope_sm_input=0.01` so the regression part
can be learned more effectively.

## 9. LGT Pyro-SVI smoke or lightweight fit

Use `pyro-svi` only with `LGT`:

```python
from orbit.models import LGT

lgt = LGT(
    response_col="y",
    date_col="ds",
    seasonality=1,
    estimator="pyro-svi",
    num_steps=100,
    num_sample=100,
    num_particles=50,
    seed=2024,
    verbose=False,
)
lgt.fit(train_df)
pred = lgt.predict(test_df)
```

For quick local validation, lower `num_steps`, `num_sample`, and
`num_particles`; for real analysis, increase them and inspect `get_training_metrics()`.

## 10. Missing response handling

ETS/LGT/DLT can fit with missing responses after the first observation because
the models substitute predictions in the one-step-ahead generation process.
Use this for gaps inside historical data:

```python
train_with_gaps = train_df.copy()
train_with_gaps.loc[gap_rows, response_col] = float("nan")
assert pd.notna(train_with_gaps[response_col].iloc[0])
model.fit(train_with_gaps)
imputed_like_pred = model.predict(train_with_gaps)
```

Do not make the first response value missing. For `LGT`, keep every non-missing
response non-negative.

## 11. Safe local workflow check

After environment setup, run the bundled smoke script:

```bash
python scripts/smoke_forecasting.py
```

It creates synthetic data in memory, runs a tiny ETS MAP forecast, checks
percentile/decomposition columns, runs a tiny LGT Pyro-SVI regressor forecast,
and validates coefficient output. It does not download data or call repository
notebooks/tests.
