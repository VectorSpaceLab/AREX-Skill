# API reference

## Verified constructor matrix

> Note: some older PyFlux docs still show a stale `ar` argument on the non-Gaussian local-level/trend pages. The runtime constructors below are the verified signatures for this skill.

| Entry point | Verified signature | Use when | Key note |
| --- | --- | --- | --- |
| `LLEV` | `LLEV(data, integ=0, target=None)` | Gaussian local level | Kalman-style fit and forecast |
| `LLT` | `LLT(data, integ=0, target=None)` | Gaussian local linear trend | Two-state local level + trend |
| `NLLEV` | `NLLEV(data, family, integ=0, target=None)` | Non-Gaussian local level | BBVI-based state-space model |
| `NLLT` | `NLLT(data, family, integ=0, target=None)` | Non-Gaussian local linear trend | BBVI-based state-space model |
| `DAR` | `DAR(data, ar, integ=0, target=None)` | Dynamic autoregression | Time-varying AR coefficients |
| `DynReg` | `DynReg(formula, data)` | Gaussian dynamic regression | Patsy formula input, fixed exogenous frame |
| `NDynReg` | `NDynReg(formula, data, family)` | Non-Gaussian dynamic regression | Formula + BBVI |
| `DynamicGLM` | `DynamicGLM(formula, data, family)` | Convenience selector | Returns `DynReg` for `Normal()`, otherwise `NDynReg` |
| `LocalLevel` | `LocalLevel(data, family, integ=0, target=None)` | Wrapper selector | Returns `LLEV` or `NLLEV` |
| `LocalTrend` | `LocalTrend(data, family, integ=0, target=None)` | Wrapper selector | Returns `LLT` or `NLLT` |

## Key method families

### Gaussian state-space classes

Applies to `LLEV`, `LLT`, `DAR`, and `DynReg`.

- `fit(method=None, **kwargs)` via `TSM.fit`.
  - Common methods: `MLE`, `PML`, `Laplace`, `M-H`, `BBVI`.
  - `DAR` and `DynReg` also accept rolling refits through `predict_is()`.
- `predict(...)`
  - `LLEV` / `LLT`: `predict(h=5, intervals=False, **kwargs)`.
  - `DAR`: `predict(h=5)`.
  - `DynReg`: `predict(h=5, intervals=False, oos_data=None, **kwargs)`.
- `plot_predict(...)`
  - `LLEV` / `LLT`: `plot_predict(h, past_values, intervals, **kwargs)`.
  - `DAR`: `plot_predict(h, past_values, intervals, **kwargs)`.
  - `DynReg`: `plot_predict(h, past_values, intervals, oos_data=None, **kwargs)`.
- `predict_is(...)` and `plot_predict_is(...)`
  - Rolling one-step or multi-step validation on prefixes of the sample.
  - `DynReg` and `DAR` refit on truncated training frames.
- `simulation_smoother(beta)`
  - Public state-draw helper for the Gaussian classes.
  - Use this instead of reaching into low-level Kalman recursion internals.

### Non-Gaussian state-space classes

Applies to `NLLEV`, `NLLT`, and `NDynReg`.

- `fit(optimizer='RMSProp', iterations=1000, print_progress=True, start_diffuse=False, **kwargs)`.
  - BBVI is the verified runtime path.
  - `optimizer` can be `RMSProp` or `ADAM`.
- `predict(...)`
  - `NLLEV` / `NLLT`: `predict(h=5)` point forecasts only.
  - `NDynReg`: `predict(h=5, oos_data=None)` point forecasts only.
- `plot_predict(...)`
  - `NLLEV` / `NLLT`: `plot_predict(h, past_values, intervals, **kwargs)`.
  - `NDynReg`: `plot_predict(h, past_values, intervals, oos_data=None, **kwargs)`.
- `predict_is(...)` and `plot_predict_is(...)`
  - Present for rolling checks.
  - `NDynReg.predict_is()` rebuilds the model on truncated prefixes.

## Data and formula notes

- `target` selects a DataFrame column name or an array index; if omitted, the first column is used.
- Formula models use Patsy. The DataFrame columns must match the formula terms exactly, including spelling and case.
- `DynReg` and `NDynReg` call `dmatrices` on `oos_data`, so the forecast frame must include the response column too; it may be `NaN` if you only need future regressors.
- `DynamicGLM`, `LocalLevel`, and `LocalTrend` are selectors: their `__new__` method returns the concrete class, so downstream code should inspect the returned instance type, not the selector name.
- Use `Normal()` for the Gaussian path; use a non-Normal family such as `Poisson()` for the non-Gaussian path.

## Output behavior to remember

- Gaussian `predict(..., intervals=True)` can include interval columns or shaded interval bands depending on the method.
- Non-Gaussian `predict()` is point-only; interval visualization is exposed through `plot_predict()` and is approximate because BBVI is mean-field.
- `DAR` prediction intervals are based on the Gaussian observation assumption and can be unrealistic for bounded counts.
