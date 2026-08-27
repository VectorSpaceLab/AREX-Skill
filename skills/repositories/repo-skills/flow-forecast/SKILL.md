---
name: flow-forecast
description: "Repository operating skill for using Flow Forecast's
  flood_forecast package for time-series forecasting, data preparation,
  training, inference, evaluation, and hydrology-oriented advanced models."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Flow Forecast Repo Skill

Use this skill when a task involves the Flow Forecast / `flood_forecast` Python package: deep time-series forecasting, classification/anomaly detection loaders, PyTorch model training, saved-model inference, forecast evaluation, Plotly/SHAP explanations, catchment embeddings, Neural ODEs, or differentiable GR4 hydrology models.

This skill is self-contained. Do not depend on the original repository checkout for runtime instructions. If a current checkout differs from [the provenance snapshot](references/repo-provenance.md), refresh this skill before relying on API details.

## Quick Orientation

- Install from PyPI when a checkout is not being edited: `python -m pip install flood-forecast`.
- Public package name in docs: `flood-forecast`.
- Python import package and setup distribution: `flood_forecast`.
- Core wrapper: `flood_forecast.time_model.PyTorchForecast`.
- Config-driven trainer: `python -m flood_forecast.trainer -p config.json`.
- Meta/autoencoder trainer: `python -m flood_forecast.meta_train -p config.json`.
- Saved-model inference helper: `flood_forecast.deployment.inference.InferenceMode`.
- Model names, losses, optimizers, scalers, and optional packages are summarized in [references/model-overview.md](references/model-overview.md).

Before using detailed workflows, run the bundled environment/import check when practical:

```bash
python scripts/check_flow_forecast_env.py --show-models
```

The check imports the package, reports PyTorch CPU/CUDA/MPS availability, and lists registry keys without reading any source checkout.

## Route Map

| User asks for... | Read next | Why |
|---|---|---|
| CSV schema checks, `forecast_history`/`forecast_length`, temporal features, interpolation, series-id, classification, variable-length, USGS/ASOS/GCS data caveats | [data-preparation](sub-skills/data-preparation/SKILL.md) | Owns loaders and preprocessing that feed training and inference. |
| Build or validate a JSON training config, choose model/loss/optimizer/scaler names, run or resume `PyTorchForecast`, use DA-RNN/NARX training, or debug device/checkpoint behavior | [training](sub-skills/training/SKILL.md) | Owns config-driven training and evaluation setup. |
| Load saved weights/configs, forecast from a date, run classification inference, compute metrics, create confidence interval plots, TorchScript export, or SHAP explanations | [inference](sub-skills/inference/SKILL.md) | Owns prediction/evaluation/deployment-facing APIs. |
| Use catchment embeddings, contrastive pretraining, CrossViViT, meta-data fusion, Neural ODEs, GR4 dynamics, HybridGR4, or hydrology-specific losses | [multimodal-physics](sub-skills/multimodal-physics/SKILL.md) | Owns advanced multimodal and physics/hybrid model surfaces. |
| Installation/import, dependency pins, optional services, backend selection, W&B/GCS credentials, or broad troubleshooting | [references/troubleshooting.md](references/troubleshooting.md) | Cross-cutting failure modes shared by multiple workflows. |

When a task spans routes, load them in data-flow order: data-preparation → training/model overview → inference; add multimodal-physics only for catchment/ODE/GR4 work.

## Operating Rules

1. Prefer CPU-safe examples unless the user explicitly asks for CUDA/MPS or the task is about device behavior. Flow Forecast can select CUDA/MPS through `device: "auto"`, but accelerator evidence is optional for most package workflows.
2. Treat GCS, USGS, ASOS, W&B, and large training loops as network/credential/long-running surfaces. Validate config and data locally first; only run remote calls after the user confirms credentials and side effects.
3. Use the bundled validation scripts before launching expensive training or inference. They catch missing config keys, impossible loader windows, bad datetime columns, and non-existent local paths without starting model training.
4. Use [references/model-overview.md](references/model-overview.md) before claiming a `model_name`, criterion, optimizer, scaler, or decoder is available. The registry is string-key based and misspellings fail at runtime.
5. For generated answers, cite bundled references or scripts from this skill rather than original repository docs/tests. Original repo tests were construction evidence, not runtime dependencies.

## Shared References And Scripts

- [references/model-overview.md](references/model-overview.md): model registry keys, major architecture families, criterion/optimizer/scaler/decoder names, optional dependency notes, and shape/config caveats.
- [references/troubleshooting.md](references/troubleshooting.md): install/import conflicts, device fallback, GCS/W&B credentials, data/config failures, SHAP/Plotly issues, and long-running training safeguards.
- [references/repo-provenance.md](references/repo-provenance.md): source commit, package version, evidence paths, and refresh conditions.
- [scripts/check_flow_forecast_env.py](scripts/check_flow_forecast_env.py): package import, registry, dependency, and backend diagnostic check.

## Non-goals

- Do not use this as a release/deployment-maintenance guide for publishing the package.
- Do not run full CI trainer matrices, remote data downloads, or W&B/GCS uploads without an explicit user request and budget.
- Do not use source checkout paths in final user instructions. If a recipe needs a helper, use a bundled script from this skill.
