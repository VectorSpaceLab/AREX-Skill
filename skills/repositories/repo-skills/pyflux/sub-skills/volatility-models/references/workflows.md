# Workflows

## 1. Synthetic GARCH baseline

Use a local synthetic return series so the workflow stays offline and repeatable.

```python
import numpy as np
import pandas as pd
import pyflux as pf

rng = np.random.default_rng(7)
n = 400
scale = np.repeat([0.5, 1.4, 0.8, 1.2], [100, 100, 100, 100])
returns = pd.DataFrame(scale * rng.standard_normal(n), columns=["ret"])

m = pf.GARCH(returns, p=1, q=1)
res = m.fit()
fcst = m.predict(h=10, intervals=True)
holdout = m.predict_is(h=10)
```

Validation steps:

- `res.summary()` prints a fit table.
- `fcst.shape[0] == 10` and `holdout.shape[0] == 10`.
- `fcst` has no NaNs.
- If `intervals=True`, check `99% >= 95% >= 5% >= 1%` on each row.
- `plot_fit()` should track absolute demeaned returns with a positive volatility curve.

## 2. Leverage and in-mean variants

Call `add_leverage()` before `fit()` so the latent-variable layout matches the asymmetric model.

```python
m = pf.EGARCH(returns, p=1, q=1)
m.add_leverage()
res = m.fit("BBVI", iterations=200)
m.plot_z([0, 3])
m.predict(h=5, intervals=True)
```

Use the same pattern for `EGARCHM`, `LMEGARCH`, `SEGARCH`, and `SEGARCHM`.

Validation steps:

- Confirm the leverage term appears in the latent-variable table after fitting.
- Keep the synthetic series short so long-memory and skew-t models stay responsive.
- Use `sample()` and `ppc()` only after `BBVI` or `M-H`.

## 3. Regression-in-mean workflow

Use a DataFrame with the response and all regressor columns required by the formula.

```python
import pandas as pd
import numpy as np
import pyflux as pf

rng = np.random.default_rng(3)
n = 250
x1 = rng.normal(size=n)
x2 = rng.normal(size=n)
y = 0.1 * x1 - 0.2 * x2 + 0.4 * rng.normal(size=n)

df = pd.DataFrame({"y": y, "x1": x1, "x2": x2})
model = pf.EGARCHMReg(df, p=1, q=1, formula="y ~ x1 + x2")
res = model.fit()
insample = model.predict_is(h=8)
```

If you need out-of-sample forecasts, provide a DataFrame with the same formula columns:

```python
oos = df.iloc[-8:].copy()
forecast = model.predict(h=8, oos_data=oos, intervals=True)
```

Validation steps:

- `predict_is(h=8)` is the preferred first check.
- `oos_data` must include every formula column.
- If `predict()` raises a shape or unpacking error, treat that path as fragile and keep the workflow on `predict_is()` until the forecast path is explicitly validated.

## 4. Long-memory and skew-t diagnostics

Use `LMEGARCH` when volatility persistence is slow to decay, and use `SEGARCH` / `SEGARCHM` when skewness matters.

```python
m = pf.LMEGARCH(returns, p=2, q=2)
res = m.fit()
pp = m.predict(h=5)
```

For skew-t models:

```python
m = pf.SEGARCH(returns, p=1, q=1)
m.add_leverage()
res = m.fit("M-H", nsims=400)
pval = m.ppc(T=np.mean)
```

Validation steps:

- Compare against a simpler `GARCH(1,1)` baseline before trusting the long-memory or skew-t specification.
- If MLE or MAP stalls on a skew-t model, switch to `BBVI` or `M-H`.
- Use a small synthetic series first; long-memory and skew-t models are slower than plain GARCH.

## Offline smoke check

Run the bundled section for a quick synthetic pass:

```bash
python ../../../scripts/smoke_pyflux_models.py --section volatility
```

Use that helper instead of the original live-data notebook examples when you need a reproducible sanity check.
