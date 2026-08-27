---
name: gluonts
description: "Use GluonTS for probabilistic time-series forecasting data
  pipelines, transformations, PyTorch/local models, evaluation, backtesting,
  shell deployment, and optional adapters."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# GluonTS repo skill

Use this skill when a task involves GluonTS time-series forecasting: `PandasDataset`, `ListDataset`, `DataEntry` fields, train/test windows, transformations, `Estimator`/`Predictor`, PyTorch forecasting models, forecast evaluation metrics, `gluonts.shell`, or optional forecasting adapters.

## Start here

1. Check the package snapshot and selected scope in [references/repo-provenance.md](references/repo-provenance.md) when freshness matters.
2. Read [references/package-overview.md](references/package-overview.md) for install commands, extras, backend boundaries, and route selection.
3. Run the environment diagnostic when imports or extras are uncertain:

```bash
python scripts/check_gluonts_env.py --check-torch --check-shell
```

For public package installs, use the smallest extra set required by the task:

```bash
pip install gluonts
pip install "gluonts[torch]"   # PyTorch estimator workflows
pip install "gluonts[shell]"   # gluonts.shell train/serve workflows
```

## Route by task

| Task signal | Read |
| --- | --- |
| DataFrames, long dataframes, item/static/dynamic columns, list/file datasets, JSON Lines, optional Arrow, or train/test windows | [sub-skills/data-pipelines/SKILL.md](sub-skills/data-pipelines/SKILL.md) |
| Transformation chains, time features, lag lists, missing-value indicators, samplers, or `InstanceSplitter` configuration | [sub-skills/transforms-features/SKILL.md](sub-skills/transforms-features/SKILL.md) |
| Estimator/Predictor concepts, local baselines, PyTorch estimators, forecast objects, persistence, CPU/GPU trainer kwargs | [sub-skills/forecasting-models/SKILL.md](sub-skills/forecasting-models/SKILL.md) |
| `make_evaluation_predictions`, `Evaluator`, item metrics, aggregate metrics, backtesting, or `gluonts.ev` metric questions | [sub-skills/evaluation-backtesting/SKILL.md](sub-skills/evaluation-backtesting/SKILL.md) |
| `python -m gluonts`, `python -m gluonts.shell`, SageMaker-style train/serve payloads, batch transform JSON Lines, or optional extension adapters | [sub-skills/deployment-extensions/SKILL.md](sub-skills/deployment-extensions/SKILL.md) |
| Cross-cutting install/import/data/backend problems | [references/troubleshooting.md](references/troubleshooting.md) |

## Common workflow skeleton

Use this sequence for end-to-end forecasting tasks:

1. Build a dataset with `PandasDataset` or `ListDataset` using the data-pipelines sub-skill.
2. Split the trailing horizon with `split(dataset, offset=-prediction_length)` or a date-based split.
3. Add transformations/time features only when a model workflow requires manual preprocessing; many estimators construct their own transformations internally.
4. Choose a local predictor for a quick baseline or a PyTorch estimator for learned global forecasting.
5. Generate forecasts with `predictor.predict(...)` or `make_evaluation_predictions(...)`.
6. Evaluate with `Evaluator` or `backtest_metrics` and inspect item metrics before trusting aggregates.
7. Persist or deploy only after the predictor and data schema are verified on a tiny local case.

## Bundled checks

| Helper | Use |
| --- | --- |
| `scripts/check_gluonts_env.py` | Imports GluonTS core and selected optional extras; can report optional CUDA availability. |
| `sub-skills/data-pipelines/scripts/dataset_split_smoke.py` | Validates `PandasDataset` + `split` behavior on deterministic local data. |
| `sub-skills/transforms-features/scripts/transform_feature_smoke.py` | Validates missing-value indicators, time features, lags, and instance splitting. |
| `sub-skills/forecasting-models/scripts/predictor_persistence_smoke.py` | Serializes/reloads a local predictor and compares deterministic forecasts. |
| `sub-skills/forecasting-models/scripts/torch_forecast_smoke.py` | Checks PyTorch estimator construction and, when requested, a tiny bounded train/predict path. |
| `sub-skills/evaluation-backtesting/scripts/evaluate_synthetic_forecast.py` | Runs a deterministic forecast evaluation/backtest smoke and optional item-metrics CSV output. |
| `sub-skills/deployment-extensions/scripts/shell_payload_validator.py` | Validates SageMaker-style JSON inference payloads before shell/serve use. |

## Boundaries and cautions

- CPU is sufficient for the verified required workflows. CUDA is optional acceleration for PyTorch training and must be probed before claiming GPU execution.
- MXNet workflows are legacy/unverified in this generated skill. If the user explicitly asks for MXNet, prepare a separate compatible environment and verify it before use.
- Optional adapters such as Prophet, R forecast, statsforecast, hierarchicalforecast, and rotbaum require their documented extras and sometimes external runtimes.
- Keep smoke tests deterministic and small. Avoid network datasets, benchmark-scale notebooks, Docker builds, AWS calls, long training, or credentialed services unless the user explicitly asks and the environment is prepared.
- Runtime guidance in this skill is self-contained. Do not require the original GluonTS repository files for ordinary package use.
