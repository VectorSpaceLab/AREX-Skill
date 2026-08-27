# PyFlux GAS API reference

Import the public API as:

```python
import pyflux as pf
```

The GAS stack is observation-driven: the latent location/intensity parameter is updated by the conditional score of the selected family. Use the family to choose the measurement distribution and link/score behavior.

## Common lifecycle

| Step | API | Notes |
| --- | --- | --- |
| Inspect priors | `model.latent_variables`, `model.plot_z(indices=...)` | `plot_z` requires fitted latent variables for meaningful values. |
| Modify priors | `model.adjust_prior(index, prior)` | Use integer indices from the latent-variable list. |
| Fit | `model.fit(method=None, **kwargs)` | GAS classes support `MLE`, `PML`, `Laplace`, `M-H`, and `BBVI`; default is `MLE`. Useful kwargs include `iterations`, `mini_batch`, `record_elbo`, `nsims`, `map_start`, and `quiet_progress`. |
| Forecast | `predict(...)`, `plot_predict(...)` | Forecast methods require a fitted model. With `intervals=True`, returned frames include `1%`, `5%`, `95%`, and `99%` prediction interval columns. |
| Backtest | `predict_is(h=5, fit_once=True, fit_method="MLE", intervals=False)` | Rolling in-sample predictions; `fit_once=False` refits at each step and is slower. |
| Bayesian checks | `sample(nsims=1000)`, `ppc(nsims=1000, T=np.mean)`, `plot_ppc(...)` | Available on non-rank GAS classes after `BBVI` or `M-H`; otherwise these methods raise because latent-variable draws are unavailable. |

For `MLE`, `PML`, `Laplace`, and `BBVI`, plotted prediction intervals are distribution-simulation intervals and do not represent full latent-variable uncertainty. Use `M-H` when full Bayesian prediction intervals are required.

## Families and data compatibility

| Family | Typical data | Notes |
| --- | --- | --- |
| `pf.Normal()` | Continuous signed series or score differences | Default robust starting point for synthetic smokes. |
| `pf.t()`, `pf.Skewt()`, `pf.Cauchy()`, `pf.Laplace()` | Heavy-tailed or outlier-prone continuous series | More parameters can make small samples slower or less stable. Skew-t examples may be better suited to Bayesian inference than MLE/MAP. |
| `pf.Poisson()` | Counts | Validate nonnegative integer-like observations before fitting. |
| `pf.Exponential()` | Positive/nonnegative intensities or durations | Validate nonnegative values; do not use for signed returns or score differences. |

PyFlux families expose `gradient_only=True` as a family constructor keyword for first-order score updates. The GASRank constructor also exposes `gradient_only`, but the practical score function is driven by the family object.

## Model constructors

| Model | Constructor | Use | Data/formula notes |
| --- | --- | --- | --- |
| `GAS` | `pf.GAS(data, ar, sc, family, integ=0, target=None)` | Univariate generalized autoregressive score recursion with `ar` autoregressive lags and `sc` score lags. | `data` can be a DataFrame or ndarray. If `target` is omitted, PyFlux uses the first DataFrame column or first array series. `integ` differences the series internally. |
| `GASX` | `pf.GASX(data, formula, ar, sc, family, integ=0)` | GAS with exogenous regressors; the latent parameter includes Patsy formula regressors plus AR/score terms. | Requires a pandas DataFrame and a Patsy formula such as `"y ~ x1 + x2"`. Forecasting needs `oos_data` with all formula columns, including the response placeholder and exogenous columns. |
| `GASReg` | `pf.GASReg(formula, data, family)` | Score-driven dynamic regression coefficients. | Requires a pandas DataFrame and Patsy formula. `result.states` represents the dynamic coefficient paths; `plot_fit()` plots fitted values and coefficients. Forecasting needs `oos_data` in the same formula-compatible format. |
| `GASLLEV` | `pf.GASLLEV(data, family, integ=0, target=None)` | Score-driven local-level model; one score/scale latent variable plus family-specific latent variables. | Use for a time-varying level without explicit AR/score lag order. `target` and `integ` behave as in `GAS`. |
| `GASLLT` | `pf.GASLLT(data, family, integ=0, target=None)` | Score-driven local-linear-trend model; level and trend are updated by score terms. | `result.states` contains level/trend-style state paths; `plot_fit()` shows fit, local level, and local trend. |
| `GASRank` | `pf.GASRank(data, team_1, team_2, family, score_diff, gradient_only=False)` | Dynamic paired-comparison/ranking model for score differences. | Requires a local DataFrame. `team_1`, `team_2`, and `score_diff` must exactly name columns. No remote CSV is required. |
| `BetatScore` | `pf.BetatScore()` | Advanced score helper exported by the GAS package. | It is not a fit-able model class; use it only when explicitly working with low-level beta-t score calculations. |

## Important methods by model

### `GAS`

- `fit(method="MLE", **kwargs)` estimates the constant, `AR(i)`, `SC(j)`, and family-specific latent variables.
- `predict(h=5, intervals=False)` returns a DataFrame indexed by shifted time values.
- `predict_is(h=5, fit_once=True, fit_method="MLE", intervals=False)` performs rolling in-sample forecasts.
- `plot_fit()`, `plot_predict()`, `plot_predict_is()`, `plot_z()`, `sample()`, and `ppc()` follow the common lifecycle.

### `GASX`

- `fit(...)` estimates `AR(i)`, `SC(j)`, and `Beta <term>` latent variables from the formula design matrix.
- `predict(h=5, oos_data=frame, intervals=False)` and `plot_predict(..., oos_data=frame)` require future rows for the exogenous variables. Provide at least `h` rows.
- Because PyFlux rebuilds the Patsy matrices from the same formula, include a response column in `oos_data` even when its values are placeholders.
- `predict_is(...)` uses held-out rows from the original DataFrame and does not need a separate `oos_data` argument.

### `GASReg`

- `fit(...)` estimates learning-rate/scale latent variables for dynamic coefficients plus family-specific variables.
- `plot_fit()` visualizes fitted values and coefficient paths.
- `predict(h=5, oos_data=frame, intervals=False)` requires the same formula columns as the training DataFrame; include a response placeholder and all exogenous columns.
- `result.states` from `fit()` stores dynamic coefficient paths for formula terms.

### `GASLLEV` and `GASLLT`

- `GASLLEV` is the score-driven local-level model; `GASLLT` adds a local trend component.
- Both use `fit(...)`, `predict(h=5, intervals=False)`, `predict_is(...)`, `plot_fit(...)`, `plot_predict(...)`, `plot_predict_is(...)`, `plot_z(...)`, `sample(...)`, and `ppc(...)`.
- Use Poisson families only for nonnegative counts; use Normal/t/Skewt/Laplace/Cauchy-style families for signed continuous level or trend series.

### `GASRank`

- `fit(method="MLE", **kwargs)` estimates home-advantage/constant, ability scale(s), and family-specific latent variables.
- `predict(team_1, team_2, neutral=False)` returns a scalar-like numeric predicted score difference for a fitted one-component model. `neutral=True` removes the fitted home-advantage/constant term.
- `plot_abilities(team_ids, **kwargs)` plots power paths for named teams or integer ids after fitting.
- `add_second_component(team_1, team_2)` adds paired second-component columns such as home/away players or goalies, resets latent variables, and requires a subsequent `fit()`.
- After adding a second component, the documented prediction form is `predict(team_1, team_2, team_1b, team_2b, neutral=False)`. Validate this path on a controlled fixture before relying on second-component predictions, because this PyFlux version's string lookup path is fragile; one-component prediction is the safest offline ranking forecast.
- GASRank is not cythonized in this version, so fitting can be slow on large competitive histories.
