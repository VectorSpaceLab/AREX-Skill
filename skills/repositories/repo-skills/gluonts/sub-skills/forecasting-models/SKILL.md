---
name: forecasting-models
description: "Choose and use GluonTS predictors, estimators, forecasts, local
  baselines, PyTorch estimators, and predictor persistence."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# forecasting-models

Use this sub-skill when the task is to select or operate GluonTS forecasting models after data has already been shaped as a GluonTS dataset.

## What this sub-skill covers

- Choosing between local predictors and trainable global estimators.
- Using `Estimator.train(...) -> Predictor` and `Predictor.predict(...) -> Forecast`.
- Reading `SampleForecast` and `QuantileForecast` outputs: samples, mean, median, quantiles, indexes, and multivariate dimensions.
- Running deterministic local baselines such as seasonal naive, identity, constant, moving-average, mean, and NPTS predictors.
- Constructing and optionally training selected PyTorch estimators with bounded `trainer_kwargs` on CPU or optional CUDA.
- Serializing and deserializing predictors with `Predictor.serialize(...)` and `Predictor.deserialize(...)`.

## Use the bundled references

- `references/model-overview.md` — model-selection guidance, local/global split, PyTorch catalog, and legacy backend caveats.
- `references/api-reference.md` — distilled signatures and key behaviors for predictors, forecasts, local predictors, and PyTorch estimators.
- `references/workflows.md` — copyable operating recipes for train/predict, baselines, forecast extraction, persistence, PyTorch trainer kwargs, and warm-starting.
- `references/troubleshooting.md` — failures around optional extras, short histories, features, quantiles, serialization, PyTorch Lightning, CUDA, and legacy MXNet.

## Bundled smoke scripts

Run these from any working directory after `gluonts` is installed:

```bash
python path/to/scripts/predictor_persistence_smoke.py --help
python path/to/scripts/predictor_persistence_smoke.py

python path/to/scripts/torch_forecast_smoke.py --help
python path/to/scripts/torch_forecast_smoke.py
python path/to/scripts/torch_forecast_smoke.py --train
```

`predictor_persistence_smoke.py` checks a checkout-independent local predictor serialize/reload workflow. `torch_forecast_smoke.py` constructs a tiny `PandasDataset` and a bounded PyTorch estimator; by default it does not train, and `--train` runs a one-epoch tiny smoke when the `torch`/Lightning extra is available.

## Routing hints

- If the task is about building `PandasDataset`, splitting train/test windows, JSON Lines, or entry schema, use the `data-pipelines` sub-skill first.
- If the task is about transformation chains, lags, time features, samplers, or instance splitters, use `transforms-features` first.
- If the task is about accuracy metrics, `Evaluator`, `backtest_metrics`, or `make_evaluation_predictions`, use `evaluation-backtesting` after producing forecasts.
- If the task is about SageMaker shell, CLI, or optional extension adapters, use `deployment-extensions`.

## Required safety posture

Use CPU-bounded examples unless the user explicitly asks for GPU. Treat CUDA as optional acceleration. Treat MXNet models as legacy/unverified in this skill scope; do not promise that MXNet workflows work unless the user provides and verifies a compatible MXNet environment.
