# Training Core Troubleshooting

Use this reference for `supervised.AutoML` training, configuration, prediction, scoring, and retraining failures. For import/install problems that happen before `from supervised import AutoML`, see `../../../references/troubleshooting.md`.

## Quick triage

1. Can Python import `supervised` and construct `AutoML`?
2. Is the `results_path` new, empty, or a valid trained run with `params.json`?
3. Did `fit()` complete and return before prediction/scoring?
4. Is `ml_task` correct for the target?
5. Are `algorithms`, `eval_metric`, `validation_strategy`, and time limits compatible with the task?
6. Is the failure actually data-schema related? If so, route to `../../data-preprocessing/`.

## Common failures and fixes

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `This model has not been fitted yet. Please call fit() first.` | Calling `predict()`, `predict_proba()`, `predict_all()`, `score()`, or `need_retrain()` before a successful fit/load. | Call `fit(X, y)` and ensure it completes, or construct `AutoML(results_path=...)` with a valid saved run. |
| `Cannot load AutoML directory` | `results_path` contains a bad or incomplete `params.json`, or model artifacts are missing. | Use a fresh output path for training, or route saved-run repair to `../../artifacts-reports/`. |
| `Directory ... is not empty` | Training path exists, has files, and is not a valid saved run. | Use a new directory, empty it after user approval, or intentionally load a valid trained `results_path`. |
| `predict_proba()` fails on regression | Probabilities exist only for classification tasks. | Use `predict()` for numeric predictions or `predict_all()` for a DataFrame with `prediction`. |
| `y must be specified` from `score()` | `score(X)` was called without labels. | Call `score(X, y)`; for unlabeled data use `predict()` and external evaluation later. |
| Invalid algorithm error | Misspelled algorithm, wrong capitalization, or not a list when needed. | Use exact names such as `"Xgboost"`, `"LightGBM"`, `"Decision Tree"`. Start with `algorithms=["Baseline"]` to isolate other issues. |
| Invalid metric error | `eval_metric` is not allowed for the current `ml_task`. | Choose from the task-specific metric table below or pass a valid custom function. |
| Validation type not implemented | `validation_strategy["validation_type"]` is not `"split"`, `"kfold"`, or `"custom"`. | Correct the validation dictionary. |
| Custom validation says `You need to specify cv` | `validation_strategy={"validation_type": "custom"}` but `fit(..., cv=...)` was omitted. | Pass a list/iterable of `(train_indices, validation_indices)` splits. |
| Training stops early or no model is usable | `total_time_limit` is too small for dataset size, selected algorithms, folds, repeats, or explain level. | Increase budget or reduce algorithms, folds, repeats, explanations, ensembling, and stacking. |
| `Compete` disables stacking unexpectedly | Short budget or split validation after validation adjustment. | Set explicit k-fold validation and a larger budget, or accept `stack_models=False`. |
| Optuna run takes far too long | `mode="Optuna"` defaulted to a large per-algorithm budget or too many algorithms. | Set `optuna_time_budget`, limit algorithms, and avoid Optuna for smoke checks. |
| Heavy backend import errors | Optional/heavy learner packages such as CatBoost, LightGBM, XGBoost, SHAP, plotting, or neural-net dependencies are absent or incompatible. | Check package installation; use `Baseline`, `Decision Tree`, or `Linear` to prove core workflow before enabling the heavy backend. |
| Missing column during prediction | Prediction data does not contain the feature columns used during fit. | Align prediction input columns to training columns; route schema details to `../../data-preprocessing/`. |

## Unfitted model and partial fit failures

Prediction methods load lazily from `results_path` if needed. If no trained model is present, they fail with an unfitted-model message.

Safe recovery pattern:

```python
automl = AutoML(results_path="AutoML_run")
automl.fit(X_train, y_train)          # must complete
labels = automl.predict(X_test)
```

If fitting failed partway through, do not assume the output directory is loadable. Use a new `results_path` unless a valid saved run with `params.json` and model folders is expected.

## `predict_proba()` on the wrong task

`predict_proba()` is only for binary and multiclass classification:

```python
if task == "regression":
    y_pred = automl.predict(X_test)
    table = automl.predict_all(X_test)  # contains prediction
else:
    y_label = automl.predict(X_test)
    y_proba = automl.predict_proba(X_test)
```

If AutoML inferred regression unexpectedly, inspect the target. A continuous or high-cardinality target leads to regression; a target with 2-20 unique values can be classified. Set `ml_task` explicitly when inference is risky.

## Algorithm mistakes

Valid algorithm strings:

```python
[
    "Baseline", "Linear", "Decision Tree", "Random Forest", "Extra Trees",
    "LightGBM", "Xgboost", "CatBoost", "Neural Network", "Nearest Neighbors",
]
```

Common corrections:

- Use `"Xgboost"`, not `"XGBoost"` or `"xgboost"`.
- Use `"Nearest Neighbors"`, not `"KNN"`.
- Pass a list, for example `algorithms=["Baseline", "Decision Tree"]`, not a comma-separated string in Python code.
- If a heavy learner fails to import or train, verify the core path with `algorithms=["Baseline"]` first.

## Metric mistakes

Allowed `eval_metric` values:

| Task | Allowed metrics |
| --- | --- |
| Binary classification | `logloss`, `auc`, `f1`, `average_precision`, `accuracy` |
| Multiclass classification | `logloss`, `f1`, `accuracy` |
| Regression | `rmse`, `mse`, `mae`, `r2`, `mape`, `spearman`, `pearson` |

Fixes:

- If the error says a metric is not allowed for the ML task, either change `eval_metric` or set the intended `ml_task` explicitly.
- For custom metrics, pass the function itself, not a placeholder string.
- Custom metrics are minimized. Return negative values for metrics that are naturally maximized.
- For classification custom metrics, handle probability-shaped predictions inside the function.

## Time-limit and budget issues

### Too little total time

Symptoms include early stopping, very few models, poor baseline-only results, or errors about stopping after the first fold.

Reduce cost:

```python
AutoML(
    algorithms=["Baseline", "Decision Tree"],
    total_time_limit=30,
    explain_level=0,
    train_ensemble=False,
    stack_models=False,
    start_random_models=1,
    hill_climbing_steps=0,
    top_models_to_improve=0,
)
```

Then increase one dimension at a time.

### `model_time_limit` overrides `total_time_limit`

If `model_time_limit` is set, `total_time_limit` is not respected. This can surprise users who expect an overall cap. Use only one of them unless the behavior is intentional.

### Folds and repeats multiply runtime

- 5-fold CV trains roughly five learners per model.
- `repeats=3` with 5 folds means about 15 learners per model.
- Stacking and ensembling add extra work after level-0 models.

### Explainability can dominate cost

Set `explain_level=0` during debugging. `explain_level=1` or `2` can require optional plotting/SHAP paths and generate larger artifacts.

## Result-directory conflicts

`results_path` behavior:

| Path state | AutoML behavior |
| --- | --- |
| Missing | Creates it. |
| Empty directory | Uses it. |
| Contains `params.json` | Tries to load an existing trained run. |
| Non-empty without `params.json` | Raises an error. |

For reproducible scripts, create one result directory per run or require an explicit overwrite flag before deleting files.

## Expensive `Compete` and `Optuna` choices

Before enabling expensive search, ask:

- How many algorithms are selected?
- Is validation split, 5-fold, 10-fold, repeated, or custom?
- Are `golden_features`, `features_selection`, `kmeans_features`, and `mix_encoding` enabled?
- Are `train_ensemble` and `stack_models` enabled?
- Is `optuna_time_budget` explicit and acceptable per algorithm?

Safe downgrade:

```python
AutoML(
    mode="Explain",
    algorithms=["Baseline", "Decision Tree"],
    explain_level=0,
    train_ensemble=False,
    stack_models=False,
)
```

## Custom CV mistakes

Custom validation requires both pieces:

```python
automl = AutoML(validation_strategy={"validation_type": "custom"})
automl.fit(X, y, cv=[(train_idx, valid_idx), ...])
```

Check:

- `cv` is a finite list or iterable; convert generators to a list if debugging.
- Every train/validation index is an integer row index into the exact `X` and `y` passed to `fit()`.
- No index is out of bounds.
- Train and validation indices are disjoint within each split unless the user intentionally accepts leakage.
- `sample_weight` and fairness `sensitive_features` have the same row order and length as `X`.
- Custom validation disables some automatic stacking-related behavior; set `stack_models=False` if uncertain.

## Heavy backend package imports

The package can import and use several heavy ML backends. Failures may happen before or during fitting when a selected algorithm needs a backend package or compiled dependency.

Isolation steps:

1. Verify the package import:

   ```python
   from supervised import AutoML
   ```

2. Train the minimal baseline:

   ```python
   AutoML(algorithms=["Baseline"], explain_level=0, train_ensemble=False, stack_models=False)
   ```

3. Add one backend algorithm at a time.
4. If only visualization/report paths fail, route to `../../artifacts-reports/` for optional Graphviz/SHAP/explainability troubleshooting.
5. If generated app serving fails because Mercury is absent, route to `../../app-deployment/`.

## Difficult usability cases to test later

- A high-cardinality mixed pandas table under a short time budget: confirm the agent routes dtype cleanup to `data-preprocessing`, disables expensive feature engineering, and starts with a minimal algorithm set.
- A regression workflow where the user asks for class probabilities: confirm the agent diagnoses the task mismatch and switches to `predict()`/`predict_all()` without suggesting unsupported probability output.
