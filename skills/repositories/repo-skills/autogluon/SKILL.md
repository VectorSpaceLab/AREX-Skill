---
name: autogluon
description: "Route AutoGluon repo tasks across tabular ML, time-series
  forecasting, multimodal AutoML, package setup, diagnostics, and saved
  predictor troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# AutoGluon Repo Skill

Use this repo skill when the user asks about AutoGluon, `autogluon.*` packages, `TabularPredictor`, `TimeSeriesPredictor`, `TimeSeriesDataFrame`, `MultiModalPredictor`, AutoMM, AutoGluon presets/models, or saved predictor troubleshooting.

AutoGluon automates machine learning for tabular, time-series, text, image, document, object detection, semantic matching, and multimodal workflows. This root skill is a router; read the focused sub-skill before writing workflow code.

## Start Here

- Read `references/package-overview.md` when choosing among packages, optional dependencies, public entry points, and CPU/GPU expectations.
- Read `references/troubleshooting.md` for install/import, optional backend, version mismatch, package extra, and cross-subpackage save/load failures.
- Read `references/repo-provenance.md` before deciding whether this skill matches a current source checkout or should be refreshed.
- Use `scripts/check_autogluon_env.py --help` for a safe import/version/backend diagnostic in the user's Python environment.

## Route By Task

| User task | Read first | Main APIs |
| --- | --- | --- |
| Supervised tabular classification/regression/quantile prediction | `sub-skills/tabular-ml/` | `autogluon.tabular.TabularPredictor`, `TabularDataset` |
| Tabular presets, hyperparameters, feature metadata, custom metrics/models, leaderboard, feature importance, refit, save/load | `sub-skills/tabular-ml/` | `fit`, `predict`, `evaluate`, `leaderboard`, `feature_importance`, `load` |
| Forecasting with item ids, timestamps, horizons, covariates, static features, probabilistic forecasts | `sub-skills/time-series-forecasting/` | `TimeSeriesDataFrame`, `TimeSeriesPredictor` |
| Text/image/document/mixed tabular+text/image AutoML, NER, semantic matching, zero-shot, feature extraction | `sub-skills/multimodal-automl/` | `MultiModalPredictor` |
| Object detection, semantic segmentation, COCO/VOC data, ONNX/TensorRT/export | `sub-skills/multimodal-automl/` | `MultiModalPredictor`, optional AutoMM deployment utilities |
| Install/import/backend/version mismatch across packages | `references/troubleshooting.md` | `scripts/check_autogluon_env.py` |

## Installation And Import Checks

AutoGluon supports Python 3.10 through 3.13 in this snapshot. Start with the public install command when the user wants the full stack:

```bash
python -m pip install autogluon
```

For narrower environments, install only the needed subpackage when possible:

```bash
python -m pip install autogluon.tabular
python -m pip install autogluon.timeseries
python -m pip install autogluon.multimodal
```

Then run a minimal import check:

```python
from autogluon.tabular import TabularPredictor
from autogluon.timeseries import TimeSeriesPredictor, TimeSeriesDataFrame
from autogluon.multimodal import MultiModalPredictor
```

Use the root diagnostic script for a safer, more complete probe:

```bash
python scripts/check_autogluon_env.py --json
```

## Choosing Safe Defaults

- Prefer CPU-safe smoke checks before expensive training, pretrained-model downloads, or GPU-only paths.
- For tabular smoke tests, use `sub-skills/tabular-ml/scripts/tabular_smoke.py` with tiny in-memory data.
- For forecasting schema checks, use `sub-skills/time-series-forecasting/scripts/validate_timeseries_frame.py` or `timeseries_smoke.py`.
- For multimodal data checks, use `sub-skills/multimodal-automl/scripts/inspect_multimodal_inputs.py` before fitting or downloading foundation-model weights.
- Load saved predictors only from trusted directories; AutoGluon predictors are pickle-backed artifacts.

## Cross-Subskill Decisions

- If the data is rows with one target column and no forecast horizon, use tabular ML even when columns include text-like strings.
- If the data has `item_id` and `timestamp` with future horizons, use time-series forecasting even when covariates are tabular.
- If the workflow needs image/document/text foundation models, semantic matching, object detection, segmentation, or zero-shot inference, use multimodal AutoML.
- If a user wants a single application combining several data types, route each modeling component to the owning sub-skill and keep shared environment/version checks at the root.

## Verification Notes

The bundled scripts are designed to be self-contained and safe by default. They do not require the original AutoGluon source checkout. Native repository tests and examples are verification evidence, not runtime dependencies for future agents.
