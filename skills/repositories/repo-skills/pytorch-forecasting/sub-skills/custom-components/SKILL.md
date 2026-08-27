---
name: custom-components
description: "Implement custom PyTorch Forecasting metrics, models, package
  wrappers, data modules, and focused maintainer tests."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Custom Components

Use this sub-skill when you are adding or reviewing PyTorch Forecasting custom components for version 1.8.0: metrics/losses, v1 `BaseModel` implementations, v1 `_pkg` package containers, experimental v2 model/package/data-module components, and focused maintainer tests.

Do not use this sub-skill for ordinary package usage, release/changelog work, broad CI administration, documentation-site builds, or hyperparameter-tuning workflows.

## Route by task

- For a custom metric or loss, start from the bundled template, then read the metric section in [references/custom-components.md](references/custom-components.md); it explains the `MultiHorizonMetric` contract, optional distribution-loss hooks, and package-wrapper tags when a metric must be discoverable.
- For a v1 custom model, read [references/custom-components.md](references/custom-components.md); it gives the `BaseModel` / `BaseModelWithCovariates` / `_pkg` pattern, `TimeSeriesDataSet.from_dataset` rules, tensor-dict shape expectations, and registry tags.
- For experimental v2 work, read [references/custom-components.md](references/custom-components.md); it summarizes the v2 `BaseModel`, `Base_pkg`, `TimeSeries`, and `EncoderDecoderTimeSeriesDataModule` concepts without relying on source templates.
- Before running checks, use [references/maintainer-testing.md](references/maintainer-testing.md); it lists focused pytest selections, CPU smoke tests, ruff/mypy/pre-commit basics, and when to avoid broad optional extras.
- When a component fails import, `.from_dataset`, tensor-shape, package-linkage, optional-dependency, or estimator tests, use [references/troubleshooting.md](references/troubleshooting.md); it maps common failure signals to fixes.
- Copy [scripts/custom_metric_template.py](scripts/custom_metric_template.py) when implementing a new point-style `MultiHorizonMetric`; it is a syntactically valid, minimal class with a CPU self-check.

## Operating stance

Prefer small CPU fixtures and package-relative commands. Keep optional dependencies behind lazy imports and explicit `python_dependencies` tags. Treat v2 APIs as beta/unstable; prefer stable v1 `TimeSeriesDataSet` + `BaseModel.from_dataset()` unless the task explicitly targets v2 package/data-module layers.
