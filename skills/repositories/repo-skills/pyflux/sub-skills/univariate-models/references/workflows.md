# Workflows

## Purpose

Practical offline recipes for ARIMA, ARIMAX, and NNAR, with validation steps that do not require network-backed data.

## 1) Plain ARIMA on a continuous synthetic series

Use this when the user wants a single-series forecast with no exogenous regressors.

```python
import numpy as np
import pyflux as pf

noise = np.random.normal(0, 1, 120)
y = np.zeros(120)
for i in range(1, len(y)):
    y[i] = 0.8 * y[i - 1] + noise[i]

model = pf.ARIMA(data=y, ar=2, ma=2, family=pf.Normal())
result = model.fit('MLE')
print(result.summary())

model.plot_fit(figsize=(12, 4))
pred = model.predict(h=8, intervals=True)
pred_is = model.predict_is(h=8, fit_once=True, fit_method='MLE', intervals=True)
```

Validation steps:
- `pred.shape[0] == 8`
- `pred_is.shape[0] == 8`
- no NaNs in either frame
- for continuous families, interval columns are strictly ordered

Evidence-derived validation behaviors:
- fitted latent variables are finite
- forecasts have the requested horizon
- continuous prediction intervals are strictly ordered

## 2) ARIMA for count data

Use this when the series is discrete counts or a count-like process.

```python
import numpy as np
import pyflux as pf

base = np.zeros(120)
for i in range(1, len(base)):
    base[i] = 0.7 * base[i - 1] + np.random.normal(0, 0.1)
counts = np.random.poisson(np.exp(base), len(base))

model = pf.ARIMA(data=counts, ar=2, ma=2, family=pf.Poisson())
result = model.fit('MLE')
pred = model.predict(h=8, intervals=True)
```

Validation steps:
- `pred.shape[0] == 8`
- no NaNs
- interval columns are non-decreasing, allowing ties
- if posterior draws or PPCs are needed, refit with `BBVI` or `M-H`

Evidence-derived validation behaviors:
- fitted latent variables are finite
- forecasts have the requested horizon
- Poisson interval bounds may tie, so use non-decreasing checks

## 3) ARIMAX with forecastable exogenous variables

Use this when the future values of regressors are known, scenario-based, or supplied in a synthetic forecast frame.

```python
import numpy as np
import pandas as pd
import pyflux as pf

n = 100
x1 = np.random.normal(size=n)
x2 = np.random.normal(size=n)
y = np.zeros(n)
noise = np.random.normal(size=n)
for i in range(1, n):
    y[i] = 0.7 * y[i - 1] + 0.2 * x1[i] - 0.1 * x2[i] + noise[i]

data = pd.DataFrame({'y': y, 'x1': x1, 'x2': x2})
model = pf.ARIMAX(data=data, formula='y~x1+x2', ar=2, ma=2, family=pf.Normal())
result = model.fit('MLE')

future = data.tail(12).copy()
future['y'] = np.nan
pred = model.predict(h=8, oos_data=future, intervals=True)
model.plot_predict(h=8, oos_data=future, past_values=20, intervals=True)
```

Validation steps:
- `future` has the same columns as `data`
- `y` may be NaN in the forecast frame
- `pred.shape[0] == 8`
- no NaNs in `pred`
- the formula should stay whitespace-free on the left side, for example `y~x1+x2`

Evidence-derived validation behaviors:
- forecast frames must preserve training columns
- forecasts and rolling predictions have the requested horizon
- interval ordering is checked separately for continuous and count families

## 4) NNAR with BBVI

Use this when a nonlinear autoregressive model is preferred and BBVI is acceptable.

```python
import numpy as np
import pyflux as pf

noise = np.random.normal(0, 1, 140)
y = np.zeros(140)
for i in range(1, len(y)):
    y[i] = 0.6 * y[i - 1] + noise[i]

model = pf.NNAR(data=y, ar=2, units=4, layers=1, family=pf.Normal())
result = model.fit('BBVI', iterations=200, quiet_progress=True, record_elbo=True)

pred = model.predict(h=8, intervals=True)
pred_is = model.predict_is(h=8, fit_once=True, fit_method='BBVI', intervals=True)
samples = model.sample(nsims=100)
ppc_value = model.ppc(nsims=100)
```

Validation steps:
- `result.elbo_records[0] < result.elbo_records[-1]` on the synthetic smoke
- `pred.shape[0] == 8`
- `samples.shape[0] == 100`
- use `fit_method='BBVI'` explicitly in `predict_is()` and `plot_predict_is()`
- if `ar=1` causes shape alignment trouble, switch to `ar=2` or higher

There are no bundled native NNAR tests in the repo; the route is validated by the verified synthetic smoke.

## 5) Common validation ladder

1. Fit the model and call `summary()`.
2. Check `plot_fit()` on a tiny synthetic series.
3. Run `predict_is()` before trusting `predict()`.
4. For ARIMAX, verify the future frame and formula handling before forecast use.
5. For Bayesian checks, call `sample()` or `ppc()` only after `BBVI` or `M-H` fit.
6. From `sub-skills/univariate-models/`, use the root smoke helper once the top-level skill tree exists:

   `../../../scripts/smoke_pyflux_models.py --section univariate`

## 6) Bayesian choice guide

- `M-H` is the safest route when you need fully Bayesian predictive intervals for ARIMA or ARIMAX.
- `BBVI` is the only supported fit for NNAR.
- BBVI intervals are useful, but they do not capture the same posterior correlation structure as `M-H`.
