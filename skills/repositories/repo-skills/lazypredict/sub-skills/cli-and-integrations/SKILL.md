---
name: cli-and-integrations
description: "Use Lazy Predict CLI and integrations for CSV classification or
  regression runs, MLflow tracking, Dask and PySpark conversion, Spark MLlib
  classes, GPU or Intel optional checks, and integration troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# CLI and Integrations

Use this sub-skill when the user wants the `lazypredict` command-line interface,
CSV target-column benchmarking, package environment checks, MLflow tracking,
Dask/PySpark conversion, Spark MLlib classes, or optional acceleration and
integration troubleshooting.

## CLI quick check

The installed console command is `lazypredict`:

```bash
lazypredict --help
lazypredict --version
```

The CLI supports supervised classification and regression from a CSV file. It
does not expose `LazyForecaster`, tuning, SHAP, or advanced integrations.

Run the bundled helper for a safe CLI command-object smoke test:

```bash
python scripts/smoke_cli.py --task classification
```

Use `--skip-fit` when only help/version behavior should be checked.

## What to read

- [references/cli-reference.md](references/cli-reference.md) for CLI flags,
  CSV assumptions, output expectations, and limitations.
- [references/integrations.md](references/integrations.md) for MLflow,
  Dask/PySpark, Spark MLlib, GPU, Intel Extension, and optional dependency
  checks.
- [references/troubleshooting.md](references/troubleshooting.md) for missing
  target columns, CLI not found, CSV data issues, MLflow/Spark/Dask/GPU
  dependency failures, and CUDA fallback semantics.

## Route elsewhere

- Use [supervised-benchmarking](../supervised-benchmarking/SKILL.md) when the
  user needs Python API control over model lists, categorical encoders, custom
  metrics, predictions, persistence, or fitted pipelines.
- Use [time-series-forecasting](../time-series-forecasting/SKILL.md) for
  `LazyForecaster`; the CLI is not a time-series interface.
- Use [advanced-workflows](../advanced-workflows/SKILL.md) for tuning,
  explainability, search spaces, SHAP, and optional plotting details.
