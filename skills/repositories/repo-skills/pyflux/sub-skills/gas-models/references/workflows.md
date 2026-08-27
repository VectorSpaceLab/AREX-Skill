# PyFlux GAS workflows

These workflows are synthetic and offline. Prefer them when you need a safe validation recipe without network access or original benchmark data.

## Shared validation checklist

1. Build a small deterministic fixture with `numpy.random.seed(...)`.
2. Fit once with `MLE` unless the task specifically needs Bayesian draws.
3. Verify fitted latent variables are finite.
4. Verify `predict(...)`/`predict_is(...)` return the expected number of rows.
5. If intervals are requested, verify the interval columns are ordered:
   `99% > 95% > mean > 5% > 1%`.
6. For count/intensity series, check `data.min() >= 0` before choosing `Poisson` or `Exponential`.

## Workflow 1: univariate GAS forecasting

Use this for a single observed series with no exogenous columns.

```python
import numpy as np
import pandas as pd
import pyflux as pf

np.random.seed(7)
y = np.zeros(200)
noise = np.random.normal(size=200)
for t in range(1, 200):
    y[t] = 0.85 * y[t-1] + noise[t]

df = pd.DataFrame({"y": y})
model = pf.GAS(data=df, ar=1, sc=1, family=pf.Normal())
res = model.fit("MLE")
forecast = model.predict(h=8)
```

Validation:

- `len(model.latent_variables.z_list)` matches the family/model setup.
- `forecast.shape[0] == 8`.
- `np.isfinite(forecast.values).all()`.

For count data, swap in `pf.Poisson()` and make the fixture nonnegative.

## Workflow 2: GASX with exogenous regressors

Use this when the future prediction depends on exogenous variables.

```python
import numpy as np
import pandas as pd
import pyflux as pf

np.random.seed(11)
n = 180
x1 = np.random.normal(size=n)
x2 = np.random.normal(size=n)
y = np.zeros(n)
for t in range(1, n):
    y[t] = 0.6 * y[t-1] + 0.3 * x1[t] - 0.2 * x2[t] + np.random.normal(scale=0.5)

df = pd.DataFrame({"y": y, "x1": x1, "x2": x2})
model = pf.GASX(data=df, formula="y ~ x1 + x2", ar=1, sc=1, family=pf.Normal())
res = model.fit("MLE")

oos = pd.DataFrame({
    "y": np.zeros(10),
    "x1": np.random.normal(size=10),
    "x2": np.random.normal(size=10),
})
forecast = model.predict(h=10, oos_data=oos)
```

Validation:

- `oos_data` contains every column referenced by the formula.
- `forecast.shape[0] == 10`.
- `forecast` is finite.

## Workflow 3: GASReg dynamic regression

Use this for time-varying coefficients rather than a fixed regression.

```python
import numpy as np
import pandas as pd
import pyflux as pf

np.random.seed(19)
n = 160
x1 = np.random.normal(size=n)
x2 = np.random.normal(size=n)
y = np.zeros(n)
for t in range(1, n):
    y[t] = 0.7 * y[t-1] + 0.4 * x1[t] - 0.1 * x2[t] + np.random.normal(scale=0.4)

df = pd.DataFrame({"y": y, "x1": x1, "x2": x2})
model = pf.GASReg(formula="y ~ x1 + x2", data=df, family=pf.t())
res = model.fit("MLE")
coef_path = getattr(res, "states", None)

oos = df.tail(8).copy()
oos["y"] = 0.0
forecast = model.predict(h=8, oos_data=oos)
```

Validation:

- `coef_path` should exist on the fitted results object.
- `forecast.shape[0] == 8` and all forecast values are finite.
- If you need uncertainty bands, rerun with `intervals=True` and check interval ordering.

## Workflow 4: local-level and local-trend GAS

Use this for score-driven smoothing of counts or continuous signals.

```python
import numpy as np
import pandas as pd
import pyflux as pf

np.random.seed(23)
count_series = pd.DataFrame({"events": np.random.poisson(3, 120)})
trend_series = pd.DataFrame({"signal": np.cumsum(np.random.normal(size=120))})

level_model = pf.GASLLEV(data=count_series, family=pf.Poisson())
level_res = level_model.fit("MLE")
level_pred = level_model.predict(h=6)

trend_model = pf.GASLLT(data=trend_series, family=pf.Normal())
trend_res = trend_model.fit("MLE")
trend_pred = trend_model.predict(h=6)
```

Validation:

- `level_pred` and `trend_pred` each have 6 rows.
- No NaNs appear in the fitted latent variables or forecasts.
- For `GASLLT`, inspect `trend_res.states` when you need the level/trend state paths.

## Workflow 5: offline GASRank paired comparison

Use this instead of any remote NFL CSV.

```python
import numpy as np
import pandas as pd
import pyflux as pf

np.random.seed(31)
games = pd.DataFrame({
    "HomeTeam": ["A", "B", "C", "A", "B", "C", "A", "C", "B", "A"],
    "AwayTeam": ["B", "C", "A", "C", "A", "B", "C", "B", "A", "B"],
    "HomeScore": [21, 17, 13, 24, 28, 14, 20, 10, 16, 19],
    "AwayScore": [14, 20, 10, 17, 21, 11, 18, 13, 15, 12],
})
games["PointsDiff"] = games["HomeScore"] - games["AwayScore"]

rank = pf.GASRank(data=games, team_1="HomeTeam", team_2="AwayTeam",
                  score_diff="PointsDiff", family=pf.Normal())
rank.fit("MLE")
pred = rank.predict("A", "B", neutral=True)
```

Optional second component:

```python
games["HomeQB"] = ["Q1", "Q2", "Q3", "Q1", "Q2", "Q3", "Q1", "Q3", "Q2", "Q1"]
games["AwayQB"] = ["Q2", "Q3", "Q1", "Q3", "Q1", "Q2", "Q3", "Q2", "Q1", "Q2"]
rank.add_second_component("HomeQB", "AwayQB")
rank.fit("MLE")
```

Validation:

- Use the exact local column names passed to `team_1`, `team_2`, `score_diff`, and any second-component columns.
- Keep repeated teams in the fixture so the ranking paths are identifiable.
- Confirm the prediction is finite and the fit does not rely on a live URL.

## Recommended smoke order

1. `GAS` with `Normal`.
2. `GASX` with a small `y ~ x1 + x2` fixture.
3. `GASReg` with the same fixture.
4. `GASLLEV` on counts, then `GASLLT` on continuous trend data.
5. `GASRank` on a local game DataFrame.
