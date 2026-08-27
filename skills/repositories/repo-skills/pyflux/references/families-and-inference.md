# Families, Priors, Inference, Results, And Aggregation

## Purpose

Read this reference when a task crosses model families: choosing a measurement distribution, adjusting priors, selecting an inference method, interpreting result objects, using posterior predictive checks, or combining compatible model forecasts.

## Universal lifecycle

```python
import pyflux as pf

model = pf.ARIMA(data=y, ar=2, ma=1, family=pf.Normal())
print(model.latent_variables)
model.adjust_prior(0, pf.Normal(0, 10))
result = model.fit("MLE")
result.summary()
forecast = model.predict(h=5)
```

The pattern is broadly shared by `TSM`-derived models:

1. Construct with data, model-design parameters, and optionally a `family`.
2. Inspect `model.latent_variables` to see names, priors, variational distributions, and transforms.
3. Call `model.adjust_prior(index, prior)` before fitting when priors matter.
4. Fit with a supported method.
5. Use `summary()`, `plot_fit()`, `predict()`, `predict_is()`, and Bayesian diagnostics as needed.

## Inference methods

| Method | Use when | Notes |
| --- | --- | --- |
| `MLE` | Fast point-estimate fit for most univariate, volatility, GAS, state-space, and GPNARX models | Default for most classes except `VAR`, `NNAR`, and non-Gaussian state-space classes. |
| `OLS` | Fast VAR baseline | Default for `VAR`; not available for most other classes. |
| `PML` | Penalized/MAP-style point estimate | Uses priors as a regularization term. |
| `Laplace` | Approximate posterior around a MAP/MLE mode | Requires invertible Hessian information; can fail for weakly identified models. |
| `M-H` | Stronger Bayesian posterior sampling and predictive intervals | Use `nsims`, `map_start`, and `quiet_progress`; slower than point estimates. |
| `BBVI` | Black-box variational inference, neural/non-Gaussian routes, faster approximate Bayesian checks | Use `iterations`, `optimizer`, `batch_size`, `mini_batch`, `learning_rate`, `record_elbo`, and quiet/progress options as supported. |

Always check `model.supported_methods` and `model.default_method` when writing generic automation. `NNAR` supports `BBVI` only. Non-Gaussian state-space classes expose their own BBVI-style `fit(optimizer=..., iterations=..., print_progress=...)` signature rather than the generic `TSM.fit` menu.

## Families and data support

| Family | Typical data | Common use |
| --- | --- | --- |
| `Normal()` | Signed continuous series | Default, easiest first smoke check. |
| `t()` | Heavy-tailed continuous series | Returns, outliers, robust residuals. |
| `Skewt()` | Skewed heavy-tailed continuous series | More fragile; prefer Bayesian methods if MLE/MAP warns or stalls. |
| `Laplace()` | Continuous series with sharper peak/heavier tails than Normal | Robust alternatives to Normal. |
| `Cauchy()` | Very heavy-tailed continuous series | Can be hard to optimize; use small smokes first. |
| `Poisson()` | Nonnegative integer/count series | Count ARIMA/GAS/state-space routes. |
| `Exponential()` | Nonnegative durations/intensities | Do not use for signed data. |
| `Flat()` | Noninformative prior helper | Appears in latent-variable defaults; use carefully. |
| `TruncatedNormal()` | Bounded priors, such as positive volatility coefficients | Useful for GARCH-style prior constraints. |
| `InverseGamma()` / `InverseWishart()` | Scale/covariance priors | Mostly advanced or multivariate prior work. |

Before fitting count or positive-support models, validate the support of the data. For Poisson examples, interval-order checks may need `>=` because discrete quantiles can tie.

## Result objects and diagnostics

`fit()` returns a result object whose type depends on the inference method. Common attributes include:

- `method`: fit method name such as `MLE`, `OLS`, `PML`, `M-H`, `BBVI`, or `Laplace`.
- `z` / `z_values`: fitted latent variables.
- `aic`, `bic`, `loglik`: available for likelihood/OLS-style results where applicable.
- `signal`, `states`, `states_var`, `scores`: model-specific fitted paths.
- `elbo_records`: available when BBVI is run with `record_elbo=True`.

Common diagnostic calls:

- `result.summary()` prints parameter or posterior summaries.
- `model.plot_z(indices=...)` inspects fitted latent variables.
- `model.plot_fit()` checks fitted values against observed data.
- `model.predict_is(h=...)` is the safest rolling backtest before `predict(h=...)`.
- `model.predict(h=..., intervals=True)` requests forecast interval columns when the class supports them.
- `model.sample(...)`, `model.ppc(...)`, `plot_sample(...)`, and `plot_ppc(...)` require a Bayesian fit (`BBVI` or `M-H`) on models that expose posterior predictive draws.

## Aggregate forecast combination

`Aggregate(learning_rate=1.0, loss_type='absolute', match_window=10)` combines compatible PyFlux model predictions using exponential weights.

Minimal pattern:

```python
agg = pf.Aggregate(learning_rate=1.0, loss_type="squared")
agg.add_model(model_1)
agg.add_model(model_2)
weights, losses, ensemble = agg.run(h=10)
summary = agg.summary(h=10)
future = agg.predict(h=5, h_train=40)
```

Operational notes:

- Add only compatible fitted/unfitted PyFlux model objects that share the same final observations. `match_window` is used to detect mismatched data.
- `run(h)` uses in-sample predictions over the final `h` observations.
- `predict(h, h_train=40)` first warms up weights on in-sample predictions, then combines out-of-sample model forecasts.
- Use enough history relative to lags and `h_train`; too-short series can raise shape or negative-dimension errors.
- `loss_type` is either `absolute` or `squared`.
- Treat aggregation as a diagnostic/comparison helper, not as proof that individual model assumptions are correct.

## Generic automation tips

- Use deterministic local synthetic fixtures for smoke checks before real data.
- Print `model.model_type`, `model.model_name`, `model.default_method`, and `model.supported_methods` in debugging scripts.
- Keep BBVI and M-H iteration counts small for smokes and intentionally larger only for real analysis.
- Use `quiet_progress=True` on generic `TSM.fit` BBVI/M-H routes where available; use `print_progress=False` for non-Gaussian state-space classes.
- If a model has formula input, make forecast frames include the response placeholder and every exogenous term used by the formula.
