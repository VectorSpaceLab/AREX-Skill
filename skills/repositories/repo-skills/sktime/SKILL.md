---
name: sktime
description: "Use sktime for time-series forecasting, classification,
  regression, clustering, transformations, detection, data interfaces,
  evaluation, benchmarking, and extension development."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# sktime

Use this repo skill when a task involves the `sktime` Python package: machine
learning with time series through a unified scikit-learn-like estimator API. It
routes forecasting, panel learning, transformations, data interfaces, detection,
distances, evaluation, benchmarking, and extension-development work.

## Install and import baseline

`sktime` 1.1.0 imports as `sktime` and supports Python `>=3.10,<3.15`.
Start with the base package:

```bash
python -m pip install sktime
python -c "import sktime; print(sktime.__version__)"
```

Install optional extras only for the workflow being used, for example
`python -m pip install "sktime[forecasting]"` or
`python -m pip install "sktime[transformations]"`. Avoid `all_extras` unless a
task truly needs broad optional estimator coverage. Read
[references/package-overview.md](references/package-overview.md) for supported
Python versions, dependency groups, estimator families, and package-wide
constraints. Run [scripts/check_env.py](scripts/check_env.py) for an offline
import and module smoke check.

## Route by task

- **Forecasting**: use [sub-skills/forecasting](sub-skills/forecasting/SKILL.md)
  for `ForecastingHorizon`, `NaiveForecaster`, exogenous variables, prediction
  intervals, reduction, global or hierarchical forecasting, update workflows,
  model selection, and forecaster backtesting.
- **Classification, regression, clustering**: use
  [sub-skills/panel-learning](sub-skills/panel-learning/SKILL.md) for panel
  estimators, `load_arrow_head`, `TimeSeriesForestClassifier`, dummy baselines,
  `TimeSeriesKMeans`, estimator tags, `predict_proba`, and panel train/test flows.
- **Transformations and pipelines**: use
  [sub-skills/transformations-pipelines](sub-skills/transformations-pipelines/SKILL.md)
  for transformers, feature extraction, differencing, imputation, lag/window
  features, `SummaryTransformer`, dunder composition, `TransformedTargetForecaster`,
  and `ForecastingPipeline`.
- **Data containers, datasets, file I/O**: use
  [sub-skills/data-interfaces](sub-skills/data-interfaces/SKILL.md) for
  scitype/mtype validation, `check_is_mtype`, `convert_to`, onboard versus
  downloaded datasets, `.ts`/`.tsf`/ARFF/UCR TSV/long formats, and tiny fixtures.
- **Detection, distances, kernels, alignment**: use
  [sub-skills/detection-distances](sub-skills/detection-distances/SKILL.md) for
  anomaly, outlier, changepoint, segmentation, detector outputs, pairwise
  distances, kernels, DTW-style choices, and alignment-related APIs.
- **Evaluation and benchmarking**: use
  [sub-skills/evaluation-benchmarking](sub-skills/evaluation-benchmarking/SKILL.md)
  for temporal splitters, forecasting/detection metrics, `evaluate`, benchmark
  setup, ranking/significance analysis, and leakage checks.
- **Extensions and maintenance**: use
  [sub-skills/extension-development](sub-skills/extension-development/SKILL.md)
  for implementing compatible estimators, extension templates, estimator tags,
  soft dependency isolation, `get_test_params`, `check_estimator`, and focused
  contribution tests.

## Common operating rules

1. Identify the sktime scitype first: `Series`, `Panel`, `Hierarchical`, or
   `Table`; then select the estimator scitype such as forecaster, classifier,
   transformer, detector, splitter, or metric.
2. Prefer a base-dependency smoke path before optional estimators. Many sktime
   estimators are soft-dependency wrappers; missing packages are usually solved
   by installing a task-specific extra or choosing a base estimator fallback.
3. Use estimator tags instead of guessing capabilities. Tags expose optional
   support for exogenous variables, missing values, multivariate data,
   probabilistic predictions, update behavior, and dependency requirements.
4. Keep temporal order intact. Forecasting evaluation and time-indexed data
   should use temporal splitters or backtesting, not random row shuffles.
5. Use the bundled helper scripts for offline checks. They use toy or onboard
   data and do not require network, model downloads, GPUs, or original notebooks.
6. For package staleness or refresh decisions, read
   [references/repo-provenance.md](references/repo-provenance.md). For
   install/import and optional-dependency failures, read
   [references/troubleshooting.md](references/troubleshooting.md).

## Optional and unverified surfaces

Deep-learning/foundation-model adapters, CUDA acceleration, TensorFlow/torch
workflows, notebook-scale examples, downloaded datasets, MLflow integrations,
and broad `all_extras` installs are optional surfaces. This skill explains how
to diagnose and route them, but it does not claim they are present in a base
environment. Verify the specific extra, hardware, data access, and model cache
before relying on those workflows.
