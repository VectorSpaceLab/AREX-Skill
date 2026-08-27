---
name: pytorch-forecasting
description: "Use PyTorch Forecasting for tabular time-series datasets, deep
  forecasting models, multi-horizon losses, tuning, beta API-v2 workflows, and
  custom components."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# PyTorch Forecasting Repo Skill

Use this skill when a task involves the `pytorch-forecasting` package or its
Python import `pytorch_forecasting`: tabular time-series data contracts,
`TimeSeriesDataSet`, Lightning-backed forecasting models, probabilistic or
quantile losses, Optuna tuning, beta API-v2 workflows, or package-specific
custom model/metric components.

Do not use this skill for generic PyTorch/Lightning training that does not use
PyTorch Forecasting APIs, generic statistical forecasting outside this package,
or release/changelog automation.

## First checks

1. Verify the active environment can import the package:

   ```python
   import pytorch_forecasting as pf
   from pytorch_forecasting import TimeSeriesDataSet, TemporalFusionTransformer, QuantileLoss
   print(pf.__version__)
   ```

2. If imports, optional extras, or backend status are unclear, run the bundled
   read-only diagnostic:

   ```bash
   python scripts/check_environment.py
   python scripts/check_environment.py --json
   ```

3. Read [references/repo-provenance.md](references/repo-provenance.md) before
   deciding whether this skill matches a current checkout or should be refreshed.

4. Read [references/package-overview.md](references/package-overview.md) for the
   v1/v2 API split, public model/metric families, optional extras, and routing
   summary.

5. Use [references/troubleshooting.md](references/troubleshooting.md) for
   install/import/backend/optional-dependency failures before routing into a
   workflow-specific troubleshooting page.

## Route by task

### Data preparation and validation

Use [sub-skills/data-pipeline/SKILL.md](sub-skills/data-pipeline/SKILL.md) when
the user has a pandas-like table and needs to declare `time_idx`, target,
`group_ids`, static/known/unknown covariates, encoders, normalizers, missing-timestep handling, train/validation/prediction datasets, or dataloaders.

Typical triggers: `TimeSeriesDataSet`, `from_dataset`, `to_dataloader`,
`GroupNormalizer`, `NaNLabelEncoder`, `allow_missing_timesteps`, target NaNs,
short series, unknown categoricals, or inference datasets with future known
covariates.

### Stable v1 forecasting models

Use [sub-skills/forecasting-models/SKILL.md](sub-skills/forecasting-models/SKILL.md)
when the user needs model selection, `.from_dataset()`, Lightning `Trainer`
setup, checkpointing, prediction, interpretation, or plotting for stable v1
model families such as `TemporalFusionTransformer`, `NBeats`, `NHiTS`,
`DeepAR`, `RecurrentNetwork`, `DecoderMLP`, `TiDEModel`, `TimeXer`, `xLSTMTime`,
or `Baseline`.

Typical triggers: choosing a model for covariates, long horizons, uncertainty,
training that freezes, `predict(return_index=True)`, checkpoint loading,
`mode="raw"`, or interpretation helpers.

### Metrics, losses, and tuning

Use [sub-skills/metrics-and-tuning/SKILL.md](sub-skills/metrics-and-tuning/SKILL.md)
when the task is about `SMAPE`, `MAE`, `QuantileLoss`, distribution losses,
`MultiLoss`, aggregated objectives, model `output_size`, non-finite losses,
learning-rate finder setup, `MQF2DistributionLoss`, or Optuna
`optimize_hyperparameters()`.

Install optional extras only when needed: `pytorch-forecasting[mqf2]` for MQF2
and `pytorch-forecasting[tuning]` for Optuna tuning.

### Experimental API-v2

Use [sub-skills/api-v2-workflows/SKILL.md](sub-skills/api-v2-workflows/SKILL.md)
only when the request explicitly mentions API-v2, D1/D2/M/P layers, v2
`TimeSeries`, `EncoderDecoderTimeSeriesDataModule`, `TslibDataModule`,
`TFT_pkg_v2`, config dictionaries, or `fit()`/`predict()` package wrappers.

API-v2 is beta/WIP in this source snapshot. For production-facing workflows,
prefer the stable v1 data/model sub-skills unless the user explicitly selects
v2.

### Custom components and focused maintainer work

Use [sub-skills/custom-components/SKILL.md](sub-skills/custom-components/SKILL.md)
when editing a PyTorch Forecasting checkout to add custom metrics/losses, v1 or
v2 model classes, package wrappers, data modules, registry tags, or focused
estimator tests.

Do not route ordinary package usage here; it is for component implementation and
focused repository-development tasks, not release management or full CI.

## Backend stance

- CPU is sufficient for package import, data validation, metric checks, API-v2
  data smoke tests, and tiny model smoke tests.
- GPU/CUDA is optional acceleration for Lightning training unless a user task
  explicitly requires backend-specific proof.
- Do not claim CUDA, ROCm, MPS, or other accelerator support until the active
  environment proves the relevant torch backend and a tiny device operation.

## Runtime helpers

- `scripts/check_environment.py` checks package imports, dependency versions,
  optional extras, and torch backend status without training or downloading.
- Sub-skills contain narrower helpers for CSV data validation, tiny v1 model
  smoke tests, metric shape checks, API-v2 data smoke tests, and custom metric
  templates.

## Refresh and provenance

This skill was generated for PyTorch Forecasting 1.8.0 at the commit recorded in
[references/repo-provenance.md](references/repo-provenance.md). Refresh if the
model list, v2 stability, optional extras, constructor signatures, public
exports, or major data/model tests changed.
