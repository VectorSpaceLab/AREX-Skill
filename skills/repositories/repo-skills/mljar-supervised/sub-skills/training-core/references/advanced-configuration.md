# Advanced Training Configuration

Use this reference when default `AutoML()` is not enough and the user needs a deliberate tradeoff between runtime, search depth, model quality, interpretability, and output size.

## Configuration strategy

1. Decide task and data readiness first. Route schema, missing values, categorical/text/datetime handling, and leakage checks to `../../data-preprocessing/`.
2. Pick the cheapest mode that can answer the user's question.
3. Limit algorithms before increasing tuning depth.
4. Set explicit time budgets before enabling `Compete`, `Optuna`, stacking, or repeated CV.
5. Keep `explain_level=0` during smoke/debug runs; increase only when report artifacts are needed.
6. Use a fresh or empty `results_path` for each new training run.

## Mode details and overrides

### `Explain`

Best for initial data understanding.

Typical defaults:

```python
AutoML(mode="Explain")
```

- Uses a 75/25 split with shuffle and classification stratification.
- Tries `Baseline`, `Linear`, `Decision Tree`, `Random Forest`, `Xgboost`, and `Neural Network` when algorithms are left on `"auto"`.
- Uses `explain_level=2` by default, which can add SHAP and other report artifacts.
- Does not run random search or hill climbing by default.

For quick training-core checks, override explanations and algorithm breadth:

```python
AutoML(
    mode="Explain",
    algorithms=["Baseline", "Decision Tree"],
    explain_level=0,
    train_ensemble=False,
    stack_models=False,
)
```

### `Perform`

Best when the goal is a production-like model rather than exhaustive search.

- Uses 5-fold CV by default.
- Uses `Linear`, `Random Forest`, `LightGBM`, `Xgboost`, `CatBoost`, and `Neural Network` on `"auto"` algorithms.
- Enables moderate tuning: `start_random_models=5`, `hill_climbing_steps=2`, `top_models_to_improve=2`.
- Uses `explain_level=1` by default.
- Defaults `max_single_prediction_time` to a 0.5 second target when not set.

### `Compete`

Best for performance competitions or final model searches with enough compute.

- Uses a broader algorithm set including `Extra Trees` and `Nearest Neighbors`.
- Defaults to higher search depth: `start_random_models=10`, `hill_climbing_steps=2`, `top_models_to_improve=3`.
- Enables ensembling and, when validation allows it, stacking.
- Uses `explain_level=0` by default.
- Can run an `adjust_validation` step under `total_time_limit` to choose split vs 5-fold vs 10-fold validation. With short budgets, stacking can be disabled automatically.

Use explicit validation if automatic adjustment would surprise the workflow:

```python
AutoML(
    mode="Compete",
    validation_strategy={
        "validation_type": "kfold",
        "k_folds": 5,
        "shuffle": True,
        "stratify": True,
    },
)
```

### `Optuna`

Best only when the user explicitly wants expensive tuning.

- Tunes selected algorithms with Optuna.
- If `optuna_time_budget` is omitted in `mode="Optuna"`, it defaults to 3600 seconds per algorithm.
- The budget is per algorithm and can be repeated across raw/feature-engineered data variants.
- Uses stacking and ensembling for trained models.

Bound it tightly:

```python
AutoML(
    mode="Optuna",
    algorithms=["LightGBM"],
    optuna_time_budget=300,
    total_time_limit=None,
    explain_level=0,
)
```

Do not use `Optuna` for smoke tests, parser checks, or user sessions without a clear compute budget.

## Algorithm selection

Exact public algorithm strings:

- `Baseline`
- `Linear`
- `Decision Tree`
- `Random Forest`
- `Extra Trees`
- `LightGBM`
- `Xgboost`
- `CatBoost`
- `Neural Network`
- `Nearest Neighbors`

Practical grouping:

| Group | Algorithms | Use |
| --- | --- | --- |
| Minimal smoke | `Baseline` | Verify install, task, target, result path, and prediction APIs quickly. |
| Fast interpretable | `Decision Tree`, `Linear` | Debug features and task behavior before heavier learners. |
| Tree ensembles | `Random Forest`, `Extra Trees` | Strong CPU baselines; slower than minimal checks. |
| Gradient boosting | `LightGBM`, `Xgboost`, `CatBoost` | Often strong on tabular data; imports and training can be heavier. |
| Other | `Neural Network`, `Nearest Neighbors` | Use when justified by data/task; may be slower or preprocessing-sensitive. |

Algorithm names are case- and spelling-sensitive. Use `"Xgboost"`, not `"XGBoost"`.

## Time limits and search depth

### `total_time_limit`

Overall training limit in seconds unless `model_time_limit` is set. AutoML may still need enough time to train at least the first learner/fold; extremely small values can stop training before a usable model exists.

### `model_time_limit`

A per-model limit. If it is not `None`, `total_time_limit` is not respected. For k-fold CV, the model limit covers all learners/folds for that model.

### Tuning-depth controls

```python
AutoML(
    start_random_models=1,
    hill_climbing_steps=0,
    top_models_to_improve=0,
)
```

- `start_random_models=1` skips the `not_so_random` random-search step.
- `hill_climbing_steps=0` skips hill climbing.
- `top_models_to_improve=0` prevents extra hill-climbing candidates.
- The rough number of models per tunable algorithm increases with random models and hill-climbing combinations; exact counts can be lower if duplicate or invalid hyperparameters are skipped.

### Explain-level cost

| `explain_level` | Effect |
| --- | --- |
| `0` | Minimal artifacts, fastest; use for smokes and budgeted searches. |
| `1` | Adds importance plots, tree plots for decision trees, and linear coefficients where applicable. Optional visualization backends can matter. |
| `2` | Adds SHAP explanations in addition to level 1; can be expensive. |

Detailed report and explainability artifact interpretation belongs to `../../artifacts-reports/`.

## Ensembling and stacking

### Ensembling

`train_ensemble=True` trains a greedy ensemble over available models at the end of the run. Disable it for fast checks:

```python
AutoML(train_ensemble=False)
```

### Stacking

`stack_models="auto"` enables stacking in `Compete` and `Optuna` when validation supports it. It is disabled by default in `Explain` and `Perform`.

Important constraints:

- Stacking is disabled for custom validation.
- Stacking is disabled for split validation in some paths.
- Short `Compete` budgets can trigger validation adjustment that disables stacking.
- Stacking adds level-1 models and can substantially increase runtime and artifact size.

For explicit control:

```python
AutoML(
    mode="Compete",
    validation_strategy={"validation_type": "kfold", "k_folds": 5},
    stack_models=True,
    train_ensemble=True,
)
```

If the task is only to validate API usage, use `stack_models=False`.

## Validation and CV design

### Split

Use for small or fast runs:

```python
{"validation_type": "split", "train_ratio": 0.8, "shuffle": True, "stratify": True}
```

### K-fold

Use for more stable estimates:

```python
{"validation_type": "kfold", "k_folds": 5, "shuffle": True, "stratify": True}
```

### Repeats

`repeats` multiplies the number of learners. It only works as intended with `shuffle=True`; when shuffle is false, repeats are disabled.

### Custom

Use when the user already owns temporal, grouped, leakage-safe, or externally defined splits:

```python
AutoML(validation_strategy={"validation_type": "custom"}).fit(X, y, cv=cv)
```

Each `cv` element must be `(train_indices, validation_indices)` for rows in the exact `X`/`y` passed to `fit()`. Do not pass data frames in the `cv` list; pass integer index arrays.

## Metrics and custom metrics

Choose a metric compatible with the ML task:

```python
AutoML(ml_task="binary_classification", eval_metric="auc")
AutoML(ml_task="multiclass_classification", eval_metric="logloss")
AutoML(ml_task="regression", eval_metric="rmse")
```

For custom metrics:

```python
def metric_to_minimize(y_true, y_predicted, sample_weight=None):
    return numeric_value

AutoML(eval_metric=metric_to_minimize)
```

AutoML minimizes custom metric output. If the natural metric is higher-is-better, return `-value`.

## Feature engineering flags

Training-core owns the budget impact; detailed feature behavior is in `../../data-preprocessing/`.

| Parameter | Budget impact |
| --- | --- |
| `golden_features` | Adds generated feature candidates and extra training steps in `Perform`/`Compete`; disable for speed. |
| `features_selection` | Adds random-feature and selected-feature steps; disable for speed. |
| `kmeans_features` | Adds k-means feature variants in `Compete`; disable for speed. |
| `mix_encoding` | Adds mixed categorical encoding variants in `Compete`; disable for speed. |
| `boost_on_errors` | Adds models focused on previous errors in `Compete`; disabled for custom validation. |

A fast bounded setting is:

```python
AutoML(
    golden_features=False,
    features_selection=False,
    kmeans_features=False,
    mix_encoding=False,
    boost_on_errors=False,
)
```

## Sample weights

`fit(..., sample_weight=...)` and `score(..., sample_weight=...)` accept arrays/Series aligned to rows. Verify length and row order after train/test splitting. If custom CV is used, sample weights are split by the same integer indices.

## Reproducibility and CPU use

- Set `random_state` for repeatable AutoML choices where supported.
- Set `n_jobs=1` for predictable tiny smokes and lower contention.
- Use `n_jobs=-1` only when the user wants to use all available CPU cores.
- Heavy backends can have their own nondeterminism; repeat critical evaluations.

## Results path policy

`results_path` controls both training output and loading:

- If `None`, AutoML creates `AutoML_1`, `AutoML_2`, and so on in the current working directory.
- If the path does not exist, AutoML creates it.
- If the path exists and is empty, AutoML uses it.
- If the path exists with `params.json`, AutoML treats it as a saved trained run.
- If the path exists, is non-empty, and lacks `params.json`, fitting raises an exception.

For details on saved artifacts and loading a trained run, route to `../../artifacts-reports/`.

## Safe escalation checklist

1. Smoke: `Baseline`, `explain_level=0`, no ensemble/stacking.
2. Add `Decision Tree` or `Linear`.
3. Add one heavier learner at a time.
4. Switch from split to k-fold only when time budget allows.
5. Re-enable `train_ensemble=True`.
6. Consider `Perform`.
7. Consider `Compete` with explicit validation and time limit.
8. Consider `Optuna` only with an explicit per-algorithm budget and user approval for the cost.
