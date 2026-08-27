---
name: evaluation-backtesting
description: "Evaluate GluonTS forecasts, compute aggregate/item metrics, use ev
  metrics, and backtest predictors without alignment mistakes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# evaluation-backtesting

Use this sub-skill when the task is to evaluate installed GluonTS predictors or already-produced forecasts, inspect aggregate and per-item metrics, or run a safe backtest on a held-out forecast horizon.

## What this sub-skill covers

- Calling `make_evaluation_predictions(...)` so each predictor sees only history before the trailing prediction window.
- Pairing forecast iterators with target iterators in the same order and with compatible period indexes.
- Computing classic aggregate and item metrics with `gluonts.evaluation.Evaluator`.
- Running the one-call `backtest_metrics(...)` wrapper for an existing `Predictor`.
- Using the newer `gluonts.ev` metric definitions through `gluonts.model.evaluate_forecasts(...)` or `evaluate_model(...)`.
- Diagnosing invalid forecasts, missing/invalid targets, frequency/seasonality issues, and target-length mismatches.

## Use the bundled references

- `references/api-reference.md` — signatures, arguments, metric keys, aggregation behavior, and `gluonts.ev` metric roles.
- `references/workflows.md` — copyable recipes for trailing holdout evaluation, backtest wrappers, item metrics, custom metrics, and `gluonts.ev` evaluation.
- `references/troubleshooting.md` — common failures around alignment, iterator lengths, NaNs, quantiles, seasonality, multiprocessing, and invalid targets.

## Safe smoke check

After installing `gluonts`, run the checkout-independent helper:

```bash
python path/to/sub-skills/evaluation-backtesting/scripts/evaluate_synthetic_forecast.py --help
python path/to/sub-skills/evaluation-backtesting/scripts/evaluate_synthetic_forecast.py
```

The script creates tiny deterministic series, evaluates a local seasonal-naive predictor with `make_evaluation_predictions` and `Evaluator`, cross-checks `backtest_metrics`, optionally writes item metrics as CSV, and prints a concise success summary. It performs no network, plotting, downloads, training, or checkout-relative reads.

## Routing hints

- If the task starts from raw pandas/list/file data, use `data-pipelines` first.
- If the task needs transformation chains, samplers, time features, or lags before prediction, use `transforms-features` first.
- If the task needs model selection, training, forecast object inspection, or predictor persistence, use `forecasting-models` before evaluation.
- If the task asks about SageMaker shell, CLI, or optional extension adapters, use `deployment-extensions`.

## Required safety posture

Keep evaluation examples CPU-only, deterministic, and small unless the user explicitly asks for benchmark-scale work. Treat CUDA as optional acceleration only. Treat MXNet examples as legacy/unverified in this skill scope; do not claim MXNet evaluation workflows are verified unless a separate compatible MXNet environment has been installed and checked.
