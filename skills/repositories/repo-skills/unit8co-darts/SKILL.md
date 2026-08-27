---
name: unit8co-darts
description: "Use Darts for Python time-series construction, preprocessing,
  forecasting, PyTorch/foundation models, anomaly detection, metrics, and
  explainability."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Darts

Use this skill when a task names Darts, `darts`, `u8darts`, Unit8 Darts, or asks for Darts-specific time-series forecasting, anomaly detection, preprocessing/covariate, metric, or explainability workflows.

## Install and import check

Darts 0.46.1 supports Python 3.10+. Choose the smallest install that matches the user's workflow:

```bash
pip install darts                    # core TimeSeries, preprocessing, statistical/regression models, anomaly, metrics
pip install "darts[torch]"           # add PyTorch neural/foundation wrapper infrastructure
pip install "darts[notorch]"         # add Prophet/LightGBM/XGBoost/CatBoost/StatsForecast families
pip install "darts[all]"             # broad install only when the user truly needs both torch and notorch extras
python - <<'PY'
import darts
from darts import TimeSeries
print(darts.__version__)
print(TimeSeries)
PY
```

For a quick environment diagnosis, run [`scripts/darts_doctor.py`](scripts/darts_doctor.py). For a tiny core forecast check without external data, run [`scripts/core_forecasting_smoke.py`](scripts/core_forecasting_smoke.py).

## Route by task

- **Build or inspect time-series data**: use [`time-series-and-data`](sub-skills/time-series-and-data/SKILL.md) for `TimeSeries.from_dataframe()`, `from_group_dataframe()`, date/frequency gaps, multivariate/stochastic shape `(time, component, sample)`, static covariates, slicing, stacking, and export checks.
- **Clean, scale, transform, or build covariates**: use [`data-processing-and-covariates`](sub-skills/data-processing-and-covariates/SKILL.md) for `MissingValuesFiller`, `Scaler`, `Pipeline`, train-only fitting, inverse transforms, generated calendar covariates, and past/future covariate span validation.
- **Choose and run non-neural forecasting models**: use [`forecasting-workflows`](sub-skills/forecasting-workflows/SKILL.md) for naive/statistical/regression/global models, `fit()`/`predict()`, covariate-capable core models, probabilistic prediction, historical forecasts, and model-selection troubleshooting.
- **Use PyTorch or foundation wrappers**: use [`torch-and-foundation-models`](sub-skills/torch-and-foundation-models/SKILL.md) for `darts[torch]`, `TCNModel`/N-BEATS/TFT-style models, chunk lengths, trainer kwargs, checkpoint directories, CPU/GPU verification, and foundation wrapper cache/download planning.
- **Score or detect anomalies**: use [`anomaly-detection`](sub-skills/anomaly-detection/SKILL.md) for `KMeansScorer`, PyOD scorers, `QuantileDetector`, threshold/IQR detectors, aggregators, `ForecastingAnomalyModel`, and score-vs-binary-output semantics.
- **Evaluate forecasts or explain models**: use [`evaluation-and-explainability`](sub-skills/evaluation-and-explainability/SKILL.md) for deterministic metrics, probabilistic quantile/interval metrics, reductions, anomaly/classification metrics, `ShapExplainer`, and headless plotting boundaries.

## Common starting routes

- New pandas data → `time-series-and-data`, then `data-processing-and-covariates` if values must be filled/scaled or covariates generated.
- Baseline forecast → `forecasting-workflows` first; add `evaluation-and-explainability` for metric/reporting details.
- Neural forecast request → verify `darts[torch]` with `torch-and-foundation-models`; do not claim CUDA/foundation execution without explicit backend/cache evidence.
- Anomaly detection request → `anomaly-detection`; route any residual forecasting model setup back to forecasting or torch.
- Installation/import or optional dependency errors → root [`references/installation-and-optional-dependencies.md`](references/installation-and-optional-dependencies.md) and [`references/troubleshooting.md`](references/troubleshooting.md).

## Shared references

- [`references/model-catalog.md`](references/model-catalog.md) maps model families to install extras and sub-skill owners.
- [`references/installation-and-optional-dependencies.md`](references/installation-and-optional-dependencies.md) records install variants, optional dependency boundaries, and backend evidence.
- [`references/troubleshooting.md`](references/troubleshooting.md) covers cross-cutting install/import, optional dependency, data, plotting, and backend failures.
- [`references/repo-provenance.md`](references/repo-provenance.md) records the source commit and evidence baseline for refresh decisions.

## Boundaries

This is a runtime package-use skill, not a Darts maintainer/release workflow. It does not cover publishing packages, building Docker images, editing CI, running long benchmarks, downloading private datasets, or executing large notebooks. Optional CUDA/GPU/TPU, foundation weight downloads, and heavy model-family extras are documented but not verified by the baseline CPU skill unless a later task proves them in the target environment.
