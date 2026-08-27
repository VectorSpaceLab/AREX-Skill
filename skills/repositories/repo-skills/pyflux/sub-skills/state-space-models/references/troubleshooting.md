# Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `LocalLevel` or `LocalTrend` gives poor fits on counts, zeros, or other bounded data | The Gaussian path was used for a non-Gaussian response | Switch to `pf.LocalLevel(df, pf.Poisson())` / `pf.LocalTrend(df, pf.Poisson())`, or call `NLLEV` / `NLLT` directly |
| `predict()` does not show interval columns for the non-Gaussian models | This is by design | Use `plot_predict()` for interval visualization, or switch to the Gaussian path if interval columns are required |
| `fit()` is slow, noisy, or the ELBO jumps around on every run | BBVI is stochastic and mean-field | Keep smoke checks short, then raise `iterations` only for final analysis; `print_progress=False` makes validation cleaner |
| `KeyError`, `PatsyError`, or missing-column errors during dynamic regression forecasting | Formula variables or `oos_data` columns do not match exactly | Rebuild the forecast DataFrame with the same column names and Patsy structure as training; include the response column too, even if it is `NaN` |
| `DynamicGLM(...)` returns an unexpected class | The selector dispatches by family type | `Normal()` returns `DynReg`; any non-Normal family returns `NDynReg` |
| A copied example shows `NLLEV(data, ar, ...)` or `NLLT(data, ar, ...)` | Older docs pages still show a stale signature | Use the runtime constructor `NLLEV(data, family, integ=0, target=None)` or `NLLT(data, family, integ=0, target=None)` |
| `No latent variables estimated!` | `predict()` or `plot_predict()` was called before fitting | Fit the model first |
| `DAR` forecast output looks unrealistic or explodes quickly | `ar` is too large for the sample size, or the series was differenced too aggressively | Reduce `ar`, increase the sample length, or reduce `integ` |
| Want score-driven local level/trend instead of Kalman-style state space | Wrong model family | Route the task to `../gas-models/` and use `GASLLEV` / `GASLLT` there |
| You are tempted to call `_ss_matrices`, `_model`, `_forecast_model`, or other recursion internals | Those are implementation details | Stay with the public constructors plus `fit`, `predict`, `predict_is`, `plot_fit`, `plot_predict`, and `simulation_smoother` |

## Fast recovery rules

- If the Gaussian model is the wrong family, switch to the wrapper form with `Normal()` or a non-Normal family and re-fit.
- If a formula forecast fails, print the exact training and forecast column names before touching the model.
- If BBVI is only needed for smoke validation, use the smallest iteration count that still produces finite latent variables and forecast output.
- If you need a stable type for downstream code, instantiate `LLEV`, `LLT`, `NLLEV`, `NLLT`, `DynReg`, `NDynReg`, or `DAR` directly instead of using the dispatch wrappers.
