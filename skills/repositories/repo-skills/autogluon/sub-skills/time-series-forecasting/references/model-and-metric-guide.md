# Model and Metric Guide

Use this guide to choose AutoGluon time-series presets, model hyperparameters, metrics, and quantile settings.

## Presets

`TimeSeriesPredictor.fit(presets=...)` configures model breadth and validation behavior.

| Preset | Use When | Notes |
| --- | --- | --- |
| `fast_training` | Quick offline validation, smoke tests, constrained CPU sessions | Uses `hyperparameters="very_light"`: `Naive`, `SeasonalNaive`, `ETS`, `Theta`, `RecursiveTabular`, `DirectTabular` with sample caps. |
| `medium_quality` | Reasonable quality with moderate time | Uses `hyperparameters="light"`: statistical/tabular models plus `TemporalFusionTransformer` and Chronos-2 small in current configs. May require deep-learning/foundation-model dependencies. |
| `high_quality` | Better accuracy with longer runtime | Uses default model set. Includes broader statistical, tabular, deep, and foundation-model coverage. |
| `best_quality` | Highest validation rigor | Uses default model set plus automatic/more robust validation-window choices. Slowest among standard presets. |
| `chronos2`, `chronos2_small` | Zero-shot Chronos-2 forecasting | Uses `Chronos2` and skips model selection. Requires model weights/backend availability. |
| `chronos2_ensemble` | Blend zero-shot and fine-tuned Chronos-2 small | Runs multiple Chronos-2 variants and can improve robustness at higher cost. |
| `bolt_tiny`, `bolt_mini`, `bolt_small`, `bolt_base` | Chronos-Bolt zero-shot forecasting | Uses `Chronos` with Bolt model aliases and skips model selection. Downloads/backends may be required. |

Aliases include `best`, `high`, `medium`, `bq`, `hq`, and `mq`.

## Hyperparameter Presets

`hyperparameters` can be a string or a model dictionary.

- `"very_light"`: `Naive`, `SeasonalNaive`, `ETS`, `Theta`, `RecursiveTabular`, and `DirectTabular` with tabular sample caps.
- `"light"`: `SeasonalNaive`, `ETS`, `Theta`, `RecursiveTabular`, `DirectTabular`, `TemporalFusionTransformer`, and Chronos-2 small.
- `"default"`: broader set including `SeasonalNaive`, `AutoETS`, `DynamicOptimizedTheta`, `RecursiveTabular`, `DirectTabular`, `TemporalFusionTransformer`, `DeepAR`, multiple `Chronos2` variants, and a `Chronos` Bolt configuration with a covariate regressor.

Dictionary form:

```python
predictor.fit(
    train_data,
    hyperparameters={
        "DeepAR": {},
        "Theta": [
            {"decomposition_type": "additive"},
            {"seasonal_period": 1},
        ],
    },
)
```

A list trains multiple variants of the same model. Use `ag_args` for names, suffixes, or model-level metadata when needed.

## Model Families

| Family | Model Names | Strengths | Watch Outs |
| --- | --- | --- | --- |
| Baselines | `Naive`, `SeasonalNaive`, `Average`, `SeasonalAverage` | Fast sanity checks and hard-to-beat baselines for simple patterns | Limited covariate usage and accuracy ceiling. |
| Statistical local models | `ETS`, `AutoETS`, `Theta`, `DynamicOptimizedTheta`, `AutoARIMA`, `ARIMA`, intermittent-demand variants | Strong for many classical series, often CPU-friendly | Local per-series fitting can be slow for many items; some models have fixed training losses. |
| Tabular global models | `DirectTabular`, `RecursiveTabular` | Use AutoGluon Tabular-style features, covariates, lags, and static features | Can need enough data across items and careful covariate dtype handling. |
| GluonTS/deep models | `DeepAR`, `TemporalFusionTransformer`, `SimpleFeedForward`, `PatchTST`, `TiDE`, `DLinear`, `WaveNet` | Learn cross-series patterns and covariate effects | More sensitive to time limits, GPU/torch availability, and dataset size. |
| Foundation models | `Chronos`, `Chronos2`, `Toto` | Zero-shot or fine-tuned forecasts from pretrained time-series models | May download weights, need specific backends, and can be slow or impossible in offline/CPU-only environments. |
| Ensembles | `WeightedEnsemble`, `SimpleAverageEnsemble`, `PerformanceWeightedEnsemble`, `PerItemWeightedEnsemble` | Combine complementary models | Adds validation and inference complexity. |

## Chronos, Chronos-2, and Toto

- `Chronos2` supports zero-shot and fine-tuning modes. It supports covariates natively and can run on CPU or GPU, though GPU is recommended for speed and fine-tuning.
- `Chronos` covers original Chronos and Chronos-Bolt aliases. Original larger Chronos models may require GPU for efficient inference; Bolt variants can run on CPU but still may download weights.
- Chronos/Chronos-Bolt do not natively model future covariates the same way as Chronos-2; AutoGluon may combine them with external covariate regressors for per-timestep effects.
- `Toto` is inference-only in AutoGluon and requires a CUDA-compatible GPU. It loads model artifacts from Hugging Face-compatible paths by default.
- For no-network workflows, do not choose Chronos/Toto unless the user confirms weights are already cached and required dependencies are installed.

## Metrics

Default metric is `WQL`, a probabilistic weighted quantile loss. Available user-facing metrics include:

| Metric | Type | Use When | Cautions |
| --- | --- | --- | --- |
| `WQL` | Quantile/probabilistic | Default for probabilistic forecasts; scale-dependent aggregate loss | Large-scale series contribute more. Equivalent to WAPE when only median quantile is used. |
| `SQL` | Quantile/probabilistic | Need scaled quantile loss across series of different magnitudes | Undefined or unstable for constant series because scaling uses historical seasonal error. |
| `MAE` | Point | Need interpretable absolute error; robust to outliers vs squared metrics | Scale-dependent; optimizes median-like forecasts. |
| `MSE`, `RMSE` | Point | Need stronger penalty for large errors | Sensitive to outliers; scale-dependent. |
| `MAPE`, `SMAPE` | Point percentage | Positive-valued business metrics | Poor with zero, near-zero, sparse, or intermittent series. |
| `MASE`, `RMSSE` | Point scaled | Compare across differently scaled series | Need meaningful seasonal period and non-constant history. |
| `WAPE` | Point aggregate percentage | Business-friendly weighted absolute percentage | Large-scale series dominate. |

Metric aliases such as `mean_absolute_error`, `weighted_quantile_loss`, and `root_mean_squared_error` are accepted and normalized.

## Quantiles and Horizon Weighting

```python
predictor = TimeSeriesPredictor(
    prediction_length=12,
    eval_metric="WQL",
    quantile_levels=[0.05, 0.1, 0.5, 0.9, 0.95],
    horizon_weight=[2.0] * 3 + [1.0] * 9,
)
```

- `quantile_levels` must be increasing decimals between 0 and 1; AutoGluon sorts the provided values.
- Forecast output columns include `mean` plus stringified quantile levels.
- `horizon_weight` must have length equal to `prediction_length`, non-negative values, and at least one positive value. It changes model selection and ensemble construction but not every model's internal training loss.
- Use `eval_metric_seasonal_period` for metrics such as `MASE`, `RMSSE`, or `SQL` when the seasonal period should not be inferred from frequency.

## HPO and Ensembling

```python
from autogluon.common import space

predictor.fit(
    train_data,
    hyperparameters={"DeepAR": {"hidden_size": space.Int(20, 100)}},
    hyperparameter_tune_kwargs={"num_trials": 5, "searcher": "auto", "scheduler": "local"},
)
```

- Search spaces require `hyperparameter_tune_kwargs`; otherwise AutoGluon raises an error.
- HPO with HyperOpt/Ray-style search may require optional dependencies.
- `enable_ensemble=True` is the default. Disable it for fastest diagnostics or when only one model is trained.
- Multi-layer ensembling uses tuple-valued `num_val_windows` and a matching list of `ensemble_hyperparameters`.

## Short-Time-Limit Recommendations

For user prompts such as “probabilistic forecasts with a short time limit and no downloads”:

```python
predictor = TimeSeriesPredictor(
    prediction_length=prediction_length,
    eval_metric="WQL",
    quantile_levels=[0.1, 0.5, 0.9],
    verbosity=0,
)
predictor.fit(
    train_data,
    hyperparameters={"Naive": {}, "SeasonalNaive": {}, "Theta": {}, "ETS": {}},
    time_limit=60,
    enable_ensemble=True,
)
```

Avoid `medium_quality`, `high_quality`, `best_quality`, `Chronos2`, `Chronos`, and `Toto` unless dependencies, weights, and runtime are confirmed.
