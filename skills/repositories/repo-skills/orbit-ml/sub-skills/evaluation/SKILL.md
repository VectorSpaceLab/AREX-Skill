---
name: evaluation
description: "Evaluates Orbit forecasts with backtests, metrics, forecast plots,
  component plots, residual diagnostics, and model-level WBIC/BIC checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Evaluation

Use this sub-skill when the user wants to compare Orbit models, run a rolling or expanding backtest, score forecasts, inspect forecast plots, decompose predictions, or check residual diagnostics and WBIC/BIC results.

## Route map

- **Backtesting and metric scoring**: read [`references/backtesting-workflows.md`](references/backtesting-workflows.md).
- **Forecast, component, and diagnostic plots**: read [`references/plotting-and-diagnostics.md`](references/plotting-and-diagnostics.md).
- **WBIC/BIC flows**: read [`references/wbic-bic.md`](references/wbic-bic.md).
- **API signatures and output columns**: read [`references/api-reference.md`](references/api-reference.md).
- **Troubleshooting**: read [`references/troubleshooting.md`](references/troubleshooting.md) when a split, metric, plot, or criterion run fails.
- **Quick smoke check**: run [`scripts/smoke_backtest.py`](scripts/smoke_backtest.py) for a tiny deterministic backtest and metric table.

## What belongs here

- `TimeSeriesSplitter` and `BackTester` setup, split summaries, and prediction collection.
- Built-in metrics and user-defined metric callables for backtest scoring.
- `plot_bt_predictions`, `plot_bt_predictions2`, `plot_predicted_data`, `plot_predicted_components`, and the residual diagnostic plot.
- EDA-style plots that help inspect the same series during evaluation when needed.
- Model-level `fit_wbic()`, `get_wbic()`, and `get_bic()` usage on already-fitted Orbit models.

## What stays out

- Model construction, feature engineering, or data-loading utilities.
- KTR or broader forecasting-model-selection guidance beyond the WBIC/BIC evaluation path itself.
- Any claim that `orbit.diagnostics.metrics.wbic()` is a usable implementation; use the model methods instead.

## Quick start

1. Prepare a model that already has `date_col`, `response_col`, `fit()`, and `predict()`.
2. Choose a split scheme with `TimeSeriesSplitter` or pass split kwargs into `BackTester`.
3. Call `fit_predict()` first, then `score()` for one or more metrics.
4. Use the plot helpers on the backtest output or on a model prediction dataframe.
5. For WBIC/BIC, call the model-level method on the fitted estimator class.

## Safe execution notes

- In headless sessions, set a non-interactive matplotlib backend or use `is_visible=False`.
- `orbit.diagnostics.plot` imports `statsmodels` at module import time, so install it before using any plot helper.
- `plot_bt_predictions2(..., export_gif=True)` needs `imageio` and an existing output directory.
- Metric callables must use Orbit's accepted argument names; see the API reference before adding a custom scorer.
