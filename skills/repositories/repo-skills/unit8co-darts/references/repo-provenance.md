# Darts repo provenance

## Purpose

Read this before deciding whether this skill is current for a checkout or installed version of Darts. If the package version, commit, install extras, public API signatures, or major evidence paths differ from this snapshot, refresh the skill from repository evidence.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-13T00:00:00Z",
  "repository": {
    "name": "darts",
    "remote_url": "https://github.com/unit8co/darts.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "080b5340366b8df25e048f4cfd11ca99e3806e97",
    "working_tree": "dirty-generated-skill-artifacts-only",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "darts",
      "version": "0.46.1",
      "python_requires": ">=3.10",
      "import_names": ["darts"]
    }
  ]
}
```

## Evidence paths

This skill was distilled from these relative source paths:

- `pyproject.toml`, `darts/__init__.py` for package metadata, version, dependency groups, and Python support.
- `README.md`, `INSTALL.md` for public installation, quick forecasting, anomaly detection, feature descriptions, and package migration notes.
- `docs/userguide/timeseries.md`, `darts/timeseries.py`, `darts/tests/test_timeseries.py`, `darts/tests/test_timeseries_static_covariates.py` for `TimeSeries` construction, shapes, static covariates, grouping, export, and edge behavior.
- `docs/userguide/covariates.md`, `darts/dataprocessing/`, `darts/tests/dataprocessing/` for preprocessing, transformers, `Pipeline`, covariate generation, and span troubleshooting.
- `docs/userguide/forecasting_overview.md`, `darts/models/forecasting/`, `darts/tests/models/forecasting/` for model families, `fit()`/`predict()` behavior, covariates, optional dependencies, and probabilistic forecasts.
- `docs/userguide/torch_forecasting_models.md`, `docs/userguide/gpu_and_tpu_usage.md`, neural/foundation model source and tests, and foundation example notebook names for PyTorch/foundation/backends.
- `darts/ad/`, `darts/tests/ad/`, and README anomaly snippets for anomaly scorers, detectors, wrappers, and evaluation boundaries.
- `darts/metrics/metrics.py`, `darts/tests/metrics/`, `darts/explainability/`, and explainability tests/examples for metrics and SHAP guidance.
- `examples/*.ipynb` as workflow evidence only. The runtime skill does not require reading or running the original notebooks.

## Verification baseline

- Baseline environment verified public import of `darts==0.46.1`, `TimeSeries`, core models, anomaly APIs, metrics, SHAP package availability, and CPU PyTorch availability.
- Required CPU workflows passed bundled smoke checks.
- Optional CPU PyTorch model construction and one-epoch tiny training passed bundled smoke checks.
- CUDA/GPU/TPU execution, foundation model weight downloads/cache, and optional model families such as Prophet, LightGBM, XGBoost, CatBoost, StatsForecast, NeuralForecast, TiRex, ONNX, Optuna, and Ray were not verified in the baseline scope.

## Refresh guidance

Refresh this skill if the installed Darts package version differs from 0.46.1, the source commit changes in public API areas above, installation extras change, `TimeSeries` constructor signatures change, model-family optional dependencies move, or Darts alters neural/foundation wrapper behavior.
