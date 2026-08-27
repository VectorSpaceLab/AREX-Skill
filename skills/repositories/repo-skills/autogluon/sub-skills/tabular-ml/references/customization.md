# Tabular Customization

This reference covers presets, model-family customization, custom metrics/models, resource controls, and optional dependency strategy for `TabularPredictor`.

## Preset Strategy

```python
predictor.fit(train_data, presets="medium_quality")
predictor.fit(train_data, presets=["good_quality", "optimize_for_deployment"])
```

Quality presets:

- `medium_quality`: fast prototype; default-style no automatic stacking.
- `good_quality`: accuracy upgrade with lighter model portfolio, `auto_stack`, refit-full, and reduced bag-fold storage for fast inference.
- `high_quality`: stronger than `good_quality`, more compute, uses zeroshot-style portfolios and refit-full.
- `best_quality`: maximum standard tabular accuracy path with automatic stacking and zeroshot portfolio.
- `extreme_quality`: state-of-the-art/high-resource path using tabular foundation models; requires optional tabular foundation-model extras and is GPU-oriented.

Utility presets:

- `optimize_for_deployment`: keep only best needed artifacts and save disk space; advanced introspection may become less informative.
- `interpretable`: rule-based interpretable models through optional imodels support.
- `ignore_text` / `ignore_text_ngrams`: disable text-derived feature generation.

Versioned and alias presets include names such as `best_quality_v150`, `high_quality_v150`, `best`, `high`, `good`, `medium`, `extreme`, and short aliases `bq`, `hq`, `gq`, `mq`, `eq`.

## Hyperparameter Presets

```python
predictor.fit(train_data, hyperparameters="light")
```

Common string presets:

- `default`: strong default model portfolio.
- `light`: smaller/faster models, often useful for deployment.
- `very_light`: even smaller/faster, with more quality tradeoff.
- `toy`: extremely small models for smoke tests only.
- `multimodal`: tabular plus text/image-capable `AG_AUTOMM`; experimental and GPU-oriented.
- `interpretable`: interpretable rule-family portfolio.
- `zeroshot`: learned model portfolio used by high-quality presets.
- `zeroshot_2025_12_18_cpu` and `zeroshot_2025_12_18_gpu`: v1.5-style CPU/GPU zeroshot portfolios.
- `zeroshot_2025_tabfm`: tabular foundation-model portfolio.
- `experimental`: unstable/experimental portfolio.

## Model Family Keys

Stable or commonly used keys:

| Key | Model family | Notes |
| --- | --- | --- |
| `GBM` | LightGBM | Strong default tabular learner; optional package may be required. |
| `CAT` | CatBoost | Strong categorical learner; optional package may be required. |
| `XGB` | XGBoost | Strong tree model; optional package may be required. |
| `RF` | RandomForest | CPU-safe scikit-learn-style baseline; supports quantile variants. |
| `XT` | ExtraTrees | CPU-safe tree baseline. |
| `KNN` | k-nearest neighbors | Simple baseline; can be memory-sensitive. |
| `LR` | linear model | Useful for linear baselines and sparse/text features. |
| `NN_TORCH` | PyTorch tabular neural net | Requires torch. |
| `FASTAI` | FastAI tabular neural net | Requires FastAI dependencies. |
| `REALMLP`, `TABM` | modern neural tabular models | Optional dependencies and resource needs vary. |
| `MITRA`, `TABICL`, `TABPFNV2` | tabular foundation models | High-resource/optional; often GPU and extra packages. |
| `AG_AUTOMM` | AutoGluon MultiModal inside tabular | Text/image/tabular multimodal; route full AutoMM workflows to `../multimodal-automl/`. |

Experimental/deprecated keys can include `FT_TRANSFORMER`, `AG_TEXT_NN`, and `AG_IMAGE_NN`. Prefer newer alternatives unless a user explicitly needs legacy behavior.

## Custom Hyperparameter Dictionary

```python
hyperparameters = {
    "GBM": [
        {},
        {"extra_trees": True, "ag_args": {"name_suffix": "XT"}},
    ],
    "RF": [
        {"criterion": "gini", "ag_args": {"name_suffix": "Gini", "problem_types": ["binary", "multiclass"]}},
        {"criterion": "squared_error", "ag_args": {"name_suffix": "MSE", "problem_types": ["regression", "quantile"]}},
    ],
    "XT": {"n_estimators": 200},
}
predictor.fit(train_data, hyperparameters=hyperparameters)
```

Rules:

- Only listed model keys are trained.
- A list of dicts under one key trains multiple model variants.
- Fixed hyperparameter values work without HPO.
- Search-space objects require `hyperparameter_tune_kwargs`; otherwise fit errors.
- `included_model_types` / `excluded_model_types` can filter a preset or dictionary without editing it.

## `ag_args`

`ag_args` controls model metadata and training eligibility:

```python
hyperparameters = {
    "GBM": {
        "learning_rate": 0.03,
        "ag_args": {
            "name_suffix": "SmallLR",
            "priority": 100,
            "problem_types": ["binary", "multiclass"],
            "disable_in_hpo": True,
        },
    }
}
```

Useful keys:

- `name`, `name_main`, `name_prefix`, `name_suffix`: model naming.
- `priority`: fit order; larger trains earlier.
- `problem_types`: restrict model to selected problem types.
- `disable_in_hpo`: train only when global HPO is off.
- `valid_stacker` / `valid_base`: allow or prevent use in stack levels.
- `hyperparameter_tune_kwargs`: per-model HPO override.

## `ag_args_fit`

`ag_args_fit` constrains how a model fits:

```python
hyperparameters = {
    "CAT": {
        "ag_args_fit": {
            "num_cpus": 2,
            "num_gpus": 0,
            "max_time_limit": 60,
            "max_memory_usage_ratio": 0.5,
        }
    }
}
```

Useful keys:

- `stopping_metric`: per-model early stopping metric.
- `max_memory_usage_ratio`: model memory tolerance relative to default.
- `max_time_limit_ratio`, `max_time_limit`, `min_time_limit`: per-model time caps.
- `num_cpus`, `num_gpus`: per-model resources.
- `max_rows`, `max_features`, `max_classes`: guardrails for expensive models.
- `problem_types`: per-model valid problem type assertion.
- `ignore_constraints`: bypass row/feature/class/problem constraints only when the user accepts the risk.

## `ag_args_ensemble`

`ag_args_ensemble` controls stack/bag ensemble behavior:

```python
hyperparameters = {
    "GBM": {
        "ag_args_ensemble": {
            "use_orig_features": True,
            "max_base_models_per_type": "auto",
            "save_bag_folds": True,
        }
    }
}
```

Useful keys:

- `use_orig_features`: whether stackers see original features in addition to stack predictions.
- `max_base_models` / `max_base_models_per_type`: cap stacker inputs.
- `num_folds`, `max_sets`, `save_bag_folds`: bagging behavior for that model.
- `fold_fitting_strategy`: sequential vs parallel fold fitting.
- `num_folds_parallel`: parallel fold count; reduce it for memory/GPU pressure.

## Custom Evaluation Metric

AutoGluon accepts metric names and scorer objects from `autogluon.core.metrics`.

```python
from autogluon.core.metrics import make_scorer

custom_metric = make_scorer(
    name="custom_accuracy",
    score_func=my_metric_function,
    optimum=1,
    greater_is_better=True,
    needs_pred=False,
)
predictor = TabularPredictor(label="target", eval_metric=custom_metric)
```

Metric guidance:

- For probability metrics such as ROC AUC or log loss, ensure the scorer expects probabilities.
- For class-label metrics such as F1, threshold calibration may matter.
- Scores in AutoGluon leaderboards are normalized to higher-is-better form.
- Validate custom metrics on a tiny known input before running long fits.

## Custom Model

AutoGluon supports custom models, but treat this as expert-only. The usual pattern is to subclass the appropriate abstract model class, implement preprocessing/fit/predict/probability behavior, and add the class to `hyperparameters`.

Design checklist:

- Implement only deterministic, local behavior; avoid network downloads inside model fit.
- Declare supported problem types.
- Respect `time_limit`, resource, and memory constraints.
- Return predictions/probabilities in the shape expected by AutoGluon for the problem type.
- Test the custom model in a small single-model fit before stacking/ensembling.
- Prefer adapting user-owned model code into the project under development, not into this skill tree.

## Optional Dependency Strategy

When optional model packages are missing:

```python
predictor.fit(
    train_data,
    hyperparameters={"RF": {}, "XT": {}},
    excluded_model_types=["CAT", "XGB", "GBM"],
)
```

Guidance:

- `RF`/`XT` can provide CPU-safe baselines when LightGBM/CatBoost/XGBoost are unavailable.
- Omit high-resource keys such as `TABPFNV2`, `TABICL`, `MITRA`, `AG_AUTOMM`, `FASTAI`, or `NN_TORCH` when their backends are unavailable.
- Use root troubleshooting for package installation details, because extras and backend compatibility are cross-package concerns.
- Keep a small successful baseline before adding optional model families back one at a time.

## GPU And Foundation Models

Use GPU intentionally:

```python
predictor.fit(
    train_data,
    presets="extreme_quality",
    time_limit=3600,
    num_gpus=1,
)
```

Cautions:

- `extreme_quality` and tabular foundation-model portfolios require optional extras and are GPU-oriented.
- `fit_strategy="parallel"` does not support GPUs in the same way as sequential fit and is not the safest GPU path.
- Foundation models can require local pretrained artifacts or network/cache access depending on installation; confirm allowed behavior before use.
- For no-network CPU environments, prefer `medium_quality`, `good_quality`, or explicit classical model dictionaries.

## HPO Customization

```python
predictor.fit(
    train_data,
    hyperparameters={"GBM": {}, "XGB": {}},
    hyperparameter_tune_kwargs={
        "num_trials": 20,
        "scheduler": "local",
        "searcher": "random",
    },
    time_limit=1800,
)
```

Rules:

- HPO needs a meaningful time budget; too little time often hurts compared with a fixed portfolio.
- Use `scheduler="local"` for straightforward local runs.
- `searcher="auto"` can use Bayesian optimization for neural models and random search elsewhere.
- With HPO, `holdout_frac` may be adjusted automatically when no tuning data is provided.
- Use per-model `ag_args.hyperparameter_tune_kwargs` to override or disable HPO for specific models.

## Deployment Customization

```python
predictor = TabularPredictor(label=label, path="ag-deploy").fit(
    train_data,
    presets=["high_quality", "optimize_for_deployment"],
    time_limit=3600,
)

# For low latency service startup:
persisted = predictor.persist(models="best", with_ancestors=True, max_memory=0.4)
```

Deployment checklist:

- Use `leaderboard(test_data, only_pareto_frontier=True)` to choose speed/accuracy tradeoffs.
- Use `refit_full` for faster inference from bagged models, then validate on held-out data.
- Use `delete_models(dry_run=True)` before deleting model directories.
- Call `save_space` only after deciding no future `fit_extra`, rich feature importance, or deep fit summaries are needed.
- Use `compile` only when compiler dependencies are installed and the target model family is supported.

## Refit And Extra Training

```python
refit_map = predictor.refit_full(model="best", set_best_to_refit_full=True)
new_models = predictor.fit_extra(hyperparameters={"GBM": {"learning_rate": 0.01}}, time_limit=300)
ensemble_models = predictor.fit_weighted_ensemble(base_models=new_models, expand_pareto_frontier=True)
```

Cautions:

- `refit_full` models have no validation score; compare on held-out test data.
- `fit_extra` needs original cached data and cannot change initial holdout/bagging/feature-generator decisions.
- `fit_weighted_ensemble` needs cached train/validation or out-of-fold data.
- Save-space/deployment cleanup can disable these workflows.

## Decision Matrix

| User goal | Recommended customization |
| --- | --- |
| Fast smoke test | `hyperparameters="toy"` or explicit `RF`/`XT`, `time_limit=30`, `num_gpus=0` |
| Strong default model | `presets="good_quality"` or `"high_quality"` with real `time_limit` |
| Maximum classical accuracy | `presets="best_quality"`, enough runtime, bagging/stacking allowed |
| GPU/foundation-model accuracy | `presets="extreme_quality"`, verified optional extras, GPU available |
| Low disk deployment | `[quality_preset, "optimize_for_deployment"]`, then validate |
| Missing optional packages | Small explicit classical dictionary; exclude missing model keys |
| Interpretability | `presets="interpretable"`, verify optional imodels dependency |
| Text columns too expensive | `presets="ignore_text"` or disable text feature-generator options |
| Binary F1/balanced accuracy | Set `eval_metric`, calibrate decision threshold, pass threshold to evaluation |
