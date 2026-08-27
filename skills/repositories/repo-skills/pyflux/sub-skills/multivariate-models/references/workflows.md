# Multivariate workflows

Use small synthetic datasets first. These models are best validated by shape, finiteness, and horizon checks before any real data run.

## Workflow 1: Baseline VAR on a two-column DataFrame

```python
import numpy as np
import pandas as pd
import pyflux as pf

rng = np.random.RandomState(7)
n = 80
x = np.zeros(n)
y = np.zeros(n)
for t in range(1, n):
    x[t] = 0.6 * x[t - 1] + rng.normal(scale=0.2)
    y[t] = 0.3 * x[t - 1] + 0.5 * y[t - 1] + rng.normal(scale=0.2)

df = pd.DataFrame({"x": x, "y": y})

model = pf.VAR(data=df, lags=2)
result = model.fit()  # default OLS

forecast = model.predict(h=5)
rolling = model.predict_is(h=5, fit_once=True, fit_method="OLS")

assert forecast.shape == (5, 2)
assert rolling.shape[0] == 5
assert np.isfinite(forecast.values).all()
assert not np.isnan(rolling.values).any()
```

Validation notes:

- Use one column per variable.
- Check that forecast columns match the original series count.
- Keep `lags` small enough that the differenced sample still has enough rows.

## Workflow 2: Differenced VAR with fixed covariance

```python
rng = np.random.RandomState(13)
levels = pd.DataFrame({"a": np.cumsum(rng.normal(size=60)),
                       "b": np.cumsum(rng.normal(size=60))})

model = pf.VAR(data=levels, lags=1, integ=1, use_ols_covariance=True)
model.fit()
fcst = model.predict(h=3)

assert fcst.shape == (3, 2)
assert np.isfinite(fcst.values).all()
```

Validation notes:

- `integ=1` differences every series before fitting.
- The returned values are forecasted on the transformed scale; if you need levels, reconstruct them outside the model.
- `use_ols_covariance=True` is useful when you want the fixed covariance path for a simple smoke test.

## Workflow 3: GPNARX on one target series with a kernel

```python
import numpy as np
import pandas as pd
import pyflux as pf

rng = np.random.RandomState(11)
n = 50
y = np.zeros(n)
for t in range(1, n):
    y[t] = 0.7 * y[t - 1] + 0.15 * np.sin(y[t - 1]) + rng.normal(scale=0.1)

df = pd.DataFrame({"y": y})

model = pf.GPNARX(data=df, ar=2, kernel=pf.SquaredExponential(), target="y")
result = model.fit()  # default MLE

forecast = model.predict(h=4)
rolling = model.predict_is(h=4, fit_once=True)

assert forecast.shape == (4, 1)
assert rolling.shape[0] == 4
assert np.isfinite(forecast.values).all()
assert not np.isnan(rolling.values).any()
```

Validation notes:

- Pass a kernel object, not a kernel name string.
- Keep the series short; GP covariance work grows quickly with sample length.
- `predict_is` on GPNARX uses the model default fit path inside the replay loop, so use it as a lightweight backtest rather than a full method comparison.

## Workflow 4: Kernel comparison on the same synthetic series

Use this when the question is about kernel choice rather than whether the model runs.

```python
import numpy as np
import pandas as pd
import pyflux as pf

rng = np.random.RandomState(23)
n = 48
y = np.zeros(n)
for t in range(1, n):
    y[t] = 0.65 * y[t - 1] + 0.18 * np.sin(2 * y[t - 1]) + rng.normal(scale=0.1)

df = pd.DataFrame({"y": y})

kernels = [
    pf.SquaredExponential(),
    pf.OrnsteinUhlenbeck(),
    pf.RationalQuadratic(),
    pf.Periodic(),
]
# ARD is exported but omitted from this smoke comparison in PyFlux 0.4.17
# because its latent-variable builder references a non-existent families.FLat.

scores = {}
for kernel in kernels:
    model = pf.GPNARX(data=df, ar=2, kernel=kernel, target="y")
    model.fit()
    pred = model.predict(h=3)
    scores[kernel.__class__.__name__] = pred
    assert np.isfinite(pred.values).all()
```

Validation notes:

- Compare kernels on the same short synthetic input.
- Use `ARD` when lag relevance may differ across lag dimensions.
- Use `Periodic` only when repeated structure is plausible.

## Smoke validation pattern

When the bundled smoke helper is available, run the multivariate section after a successful fit on synthetic data.

- `../../../scripts/smoke_pyflux_models.py --section multivariate`

Checklist:

- No NaNs in latent variables or predictions.
- Forecast output length equals the requested horizon.
- VAR output has one column per input variable.
- GPNARX output has one column for the target series.
