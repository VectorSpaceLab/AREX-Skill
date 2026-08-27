# GluonTS package overview

## Purpose

Use this reference when a task needs the broad shape of GluonTS before choosing a focused sub-skill. It distills the installed package and selected repository evidence into a self-contained operating map.

## What GluonTS provides

GluonTS is a Python package for probabilistic time-series forecasting. Its stable user-facing surfaces in this skill are:

- Dataset construction and slicing: `PandasDataset`, `ListDataset`, file-backed JSON Lines datasets, and `split`/`TestTemplate` rolling windows.
- Transformation and feature pipelines: `Transformation`, `Chain`, time features, lag lists, observed-value indicators, and instance splitters/samplers.
- Forecasting objects and models: `Predictor`, `Estimator`, `Forecast`, local baseline predictors, and PyTorch Lightning-based estimators such as DeepAR, SimpleFeedForward, TemporalFusionTransformer, PatchTST, DLinear, and LagTST.
- Evaluation and backtesting: `make_evaluation_predictions`, `Evaluator`, `backtest_metrics`, aggregate/item metrics, and the newer `gluonts.ev` metric layer.
- Deployment and optional integrations: `python -m gluonts`, `python -m gluonts.shell`, SageMaker-style train/serve containers, and optional external adapters.

## Installation and extras

For ordinary package use:

```bash
pip install gluonts
```

For current neural forecasting workflows, install the PyTorch extra:

```bash
pip install "gluonts[torch]"
```

For shell/SageMaker-style train/serve workflows:

```bash
pip install "gluonts[shell]"
```

Common optional groups and their role:

| Extra | Use when |
| --- | --- |
| `torch` | PyTorch estimators, `gluonts.torch`, Lightning training/prediction. |
| `shell` | `python -m gluonts.shell train` and `serve`, local container-style serving contracts. |
| `arrow` | Arrow/Parquet-backed dataset files. |
| `pro` | Faster JSON backends (`orjson`) and Arrow support. |
| `sagemaker` | SageMaker SDK integration around shell workflows. |
| `prophet`, `R`, `statsforecast`, `hierarchicalforecast`, `rotbaum` | Optional external model adapters. |

Do not install broad `dev`/`docs`/`test` extras for ordinary use unless the task explicitly requires repository development, documentation build, or test execution.

## Minimal import and version checks

```bash
python - <<'PY'
import gluonts
from gluonts.dataset.pandas import PandasDataset
from gluonts.evaluation import Evaluator
print(gluonts.__version__)
print(PandasDataset, Evaluator)
PY
```

The package CLI is intentionally small:

```bash
python -m gluonts --help
python -m gluonts version
```

Use the skill-owned helper for a broader import check:

```bash
python scripts/check_gluonts_env.py --check-torch --check-shell
```

## Route map

| Task signal | Read |
| --- | --- |
| DataFrames, dictionaries, JSON Lines, static/dynamic features, train/test windows | `sub-skills/data-pipelines/SKILL.md` |
| Transformation chains, missing values, time features, lag lists, instance samplers/splitters | `sub-skills/transforms-features/SKILL.md` |
| Estimator/Predictor concepts, local predictors, PyTorch models, forecast objects, persistence | `sub-skills/forecasting-models/SKILL.md` |
| Evaluation iterators, aggregate/item metrics, backtesting, `gluonts.ev` metrics | `sub-skills/evaluation-backtesting/SKILL.md` |
| `python -m gluonts`, `gluonts.shell`, SageMaker-style payloads, optional adapters | `sub-skills/deployment-extensions/SKILL.md` |

## Backend and optional dependency boundaries

The verified required scope is CPU-capable GluonTS with selected PyTorch and shell dependencies. CPU execution is enough to validate API correctness, dataset preparation, local predictors, evaluation, and tiny PyTorch examples.

CUDA is optional acceleration for PyTorch training. Use CUDA only when the user asks for GPU execution or performance; otherwise keep examples CPU-bounded and deterministic.

MXNet modules may appear in older model tables and legacy code. This skill does not claim MXNet workflows are verified. If a task specifically asks for MXNet estimators, treat it as a separate optional/legacy environment task: install a compatible MXNet stack, verify imports, and run a bounded MXNet-specific smoke before relying on it.

External adapters (`prophet`, `R`, `statsforecast`, `hierarchicalforecast`, `rotbaum`) are optional. Name the exact extra/package, verify the import, and keep failure messages explicit instead of treating missing adapters as GluonTS core failures.
