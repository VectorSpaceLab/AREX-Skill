---
name: informer2020
description: "Use for Informer2020 long-sequence time-series forecasting
  training, evaluation, custom CSV preparation, and prediction workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Informer2020

Use this repo skill when a task involves the Informer2020 PyTorch implementation for long-sequence time-series forecasting: training/testing Informer or InformerStack, reproducing benchmark-style runs, preparing a custom time-series CSV, or running future prediction.

This is a source-style research repository, not a normal installable package. Treat the generated skill as the operating manual and use the bundled helpers below instead of reopening or executing original repo scripts directly.

## First checks

1. Confirm the checkout contains the Informer2020 source modules (`models`, `data`, `exp`, `utils`) and the forecasting launcher.
2. Prepare a Python environment with PyTorch, NumPy, pandas, and the documented scientific stack. For exact historical reproduction, prefer the repository's legacy pins; for smoke validation, run the bundled helpers first.
3. Run a minimal import check from the checkout or with the checkout on `PYTHONPATH`:

```bash
python - <<'PY'
from models.model import Informer, InformerStack
from data.data_loader import Dataset_Custom, Dataset_Pred
print('Informer2020 imports OK')
PY
```

4. For a safe custom-data proof, generate and validate a tiny CSV before any long training run.

## Route by task

| User task | Read |
| --- | --- |
| Train/test Informer or InformerStack, choose attention/model lengths, adapt benchmark presets, inspect metrics/checkpoints, or debug runtime training failures | [`sub-skills/training-and-evaluation/SKILL.md`](sub-skills/training-and-evaluation/SKILL.md) |
| Prepare a custom CSV, choose `S`/`M`/`MS`, validate `target`/`cols`/`freq`, run `do_predict`, or debug data-loader/prediction output issues | [`sub-skills/custom-data-and-prediction/SKILL.md`](sub-skills/custom-data-and-prediction/SKILL.md) |
| Set up dependencies, understand legacy version pins, or decide CPU/CUDA behavior | [`references/install.md`](references/install.md) |
| Debug cross-cutting install, import, data, backend, or helper-script failures | [`references/troubleshooting.md`](references/troubleshooting.md) |
| Check source snapshot and evidence paths before deciding whether the skill is stale | [`references/repo-provenance.md`](references/repo-provenance.md) |

## Bundled helpers

- [`scripts/make_tiny_forecast_csv.py`](scripts/make_tiny_forecast_csv.py): create a deterministic custom forecasting CSV with a `date` column, covariates, and a target.
- [`scripts/check_forecast_csv.py`](scripts/check_forecast_csv.py): validate custom CSV columns, feature mode, row counts, and frequency before launch.
- [`scripts/run_forecasting_smoke.py`](scripts/run_forecasting_smoke.py): generate a tiny fixture and dry-run or execute a short train/test/predict smoke command from a checkout.

Use the helpers for validation and smoke checks; use the sub-skills for larger runs and task-specific interpretation.

## Key behavior to remember

- The forecasting launcher trains and tests for every repeat; prediction is an extra branch enabled by `do_predict`.
- Built-in dataset names override CSV file name, target, and tensor widths. Custom data requires you to set dimensions yourself.
- `M`, `S`, and `MS` change both loader behavior and output width.
- The code auto-selects CUDA when visible. To force CPU reliably, hide CUDA or use the smoke helper's CPU backend option rather than relying on a string `False` value.
- Output directories are fingerprinted by the run setting. Checkpoints, metrics, test predictions, and future predictions are different files.

## Avoid this skill when

- The task is about a different forecasting library or a general time-series theory question with no Informer2020 implementation surface.
- The task is repository maintenance unrelated to forecasting workflows; use a repository-maintenance skill instead.
- The user needs a production forecasting service, model registry, or MLOps deployment stack rather than this research implementation.
