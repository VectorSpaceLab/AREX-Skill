---
name: evaluation-benchmarking
description: "Use sktime splitters, metrics, model_evaluation.evaluate, and
  benchmarking tools for leakage-aware evaluation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Evaluation and Benchmarking

Use this sub-skill for backtesting, temporal cross-validation, forecasting and detection metrics, benchmark setup, result storage, and leakage-aware experiment design in `sktime`.

## Route here

- Choose temporal, cutoff, expanding, sliding, or instance splitters.
- Score forecasts or detections with functions/classes from `sktime.performance_metrics`.
- Use `sktime.forecasting.model_evaluation.evaluate` for leakage-aware forecaster evaluation.
- Configure small `ForecastingBenchmark`, `ClassificationBenchmark`, or `RegressionBenchmark` runs and analyzers.

## Route away

Estimator construction routes to `forecasting` or `panel-learning`. Raw data layout routes to `data-interfaces`.

## Operating path

1. Identify whether the split is temporal or instance-level.
2. Choose metrics whose required inputs match the prediction type.
3. Start with a tiny single-estimator evaluation and `error_score="raise"`.
4. Expand benchmark grids only after the smoke path works and output storage is explicit.

## References and helper

- [API reference](references/api-reference.md) for splitters, metrics, `evaluate`, benchmarks, storage, and analyzers.
- [Workflows](references/workflows.md) for leakage-safe recipes and tiny benchmark patterns.
- [Troubleshooting](references/troubleshooting.md) for split leakage, metric shape, backend, and benchmark runtime issues.
- Run [scripts/evaluation_smoke.py](scripts/evaluation_smoke.py) for a tiny offline evaluation and benchmark smoke.
