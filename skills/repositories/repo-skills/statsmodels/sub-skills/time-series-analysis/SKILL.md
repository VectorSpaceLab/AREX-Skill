---
name: time-series-analysis
description: "Use statsmodels time-series APIs for stationarity tests,
  AR/ARIMA/SARIMAX, state-space models, VAR/VECM, exponential smoothing,
  STL/MSTL, filters, forecasting, and time-series troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Time-series analysis

Use this sub-skill for `statsmodels.tsa` tasks: stationarity/autocorrelation tests, AR/AutoReg, ARDL/UECM, ARIMA/SARIMAX, state-space models, VAR/SVAR/VECM, DynamicFactor, ETS/Holt-Winters, STL/MSTL decomposition, filters, forecasting, Markov switching, and X-13/X-12 integration.

## Workflow

1. Validate the time index and frequency. Forecasting is more reliable when a pandas Series/DataFrame has a monotonic date/period index with known frequency.
2. Decide the task: test, filter/decompose, univariate forecast, regression with AR errors/exogenous variables, multivariate VAR/VECM, or custom state-space.
3. Fit a small baseline model first. Inspect convergence, stationarity/invertibility restrictions, residual diagnostics, and forecast intervals.
4. Treat X-13/X-12 as optional external-binary functionality. Do not promise it from package import alone.

## Read or run

- Read [references/api-reference.md](references/api-reference.md) for `tsa` import names and verified constructor signatures.
- Read [references/workflows.md](references/workflows.md) for stationarity checks, ARIMA/SARIMAX, STL/ETS, VAR, and forecast recipes.
- Read [references/troubleshooting.md](references/troubleshooting.md) for missing frequency, convergence, stationarity/invertibility, exogenous forecast, and X-13 problems.
- Run [scripts/smoke_time_series.py](scripts/smoke_time_series.py) for a deterministic ARIMA/STL/ADF smoke check.

## Boundaries

- Route ordinary cross-sectional regression to [linear-and-formula-models](../linear-and-formula-models/SKILL.md).
- Route residual tests, Ljung-Box interpretation, or generic hypothesis-test selection to [statistical-tests-and-diagnostics](../statistical-tests-and-diagnostics/SKILL.md) when the model itself is not time-series-specific.
- Route plots and result export to [datasets-results-graphics](../datasets-results-graphics/SKILL.md) after choosing the time-series model.
