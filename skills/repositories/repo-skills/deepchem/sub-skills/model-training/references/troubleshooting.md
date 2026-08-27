# Model Training Troubleshooting

## Optional backend warnings

Symptoms:
- Importing DeepChem warns that TensorFlow, PyTorch, JAX, DGL, PyTorch Geometric, XGBoost, or LightGBM features are unavailable.
- Importing a model class fails even though `import deepchem` succeeds.

Response:
1. Treat base DeepChem import as insufficient proof that neural or GBDT models are available.
2. Pick `SklearnModel` for a runnable baseline when only base dependencies are present.
3. Gate optional examples with explicit imports and clear errors.
4. Do not install heavy extras unless the user requested that backend or approved environment changes.

## Classification metric shape errors

Common cause: using class labels where ROC-AUC expects probabilities, or using probabilities where a thresholded metric expects labels.

Fixes:
- For ROC-AUC/PRC-AUC, use classifiers with `predict_proba()` and predictions normalized to `(N, n_tasks, n_classes)` when possible.
- For label metrics such as F1, recall, Matthews correlation, or balanced accuracy, set `classification_handling_mode="threshold"` or choose an estimator/metric path that returns labels.
- Pass `mode="classification"` explicitly for custom metric wrappers.
- For binary single-task labels shaped `(N,)`, set `n_tasks=1` if DeepChem cannot infer task count.

Minimal diagnostic:

```python
metric = dc.metrics.Metric(dc.metrics.roc_auc_score, mode="classification", n_tasks=1)
print(dataset.y.shape, model.predict(dataset).shape)
print(model.evaluate(dataset, [metric], n_classes=2))
```

## Regression metric shape errors

Symptoms: unexpected squeeze behavior, `n_tasks` assertion failures, or scorer errors.

Fixes:
- Ensure labels are numeric and shape to `(N,)`, `(N, 1)`, or `(N, n_tasks)`.
- Avoid accidental `(N, 1, 1)` labels unless the metric explicitly supports it.
- Use `Metric(..., mode="regression", n_tasks=expected_tasks)` for custom or ambiguous metric functions.
- For transformed labels, pass output transformers into `evaluate()` and hyperparameter search.

## `model_dir` and persistence problems

- `model_dir=None` creates a temporary directory that may be deleted with the model object; use an explicit directory for reusable models.
- `SklearnModel.save()` writes a joblib estimator. Reload with `SklearnModel(None, model_dir=...)` followed by `reload()`.
- Neural wrappers usually need the same architecture recreated before `restore()` can load checkpoints.
- Do not mix checkpoints from different architectures, task counts, featurizer dimensions, or modes.

## Weights and sklearn estimators

`SklearnModel.fit()` tries to pass squeezed sample weights to estimators that accept `sample_weight`. If an estimator does not support weights or fails unexpectedly, construct with `use_weights=False`.

```python
model = dc.models.SklearnModel(estimator, use_weights=False)
```

## Expensive or unstable training

- Start with a tiny dataset and `SklearnModel` smoke test before launching neural training.
- Keep hyperparameter grids small; DeepChem search is serial.
- Use `RandomHyperparamOpt(..., max_iter=...)` to cap candidate count.
- For neural models, lower `nb_epoch`, batch size, and model width for debugging.
- Use validation callbacks/checkpoints rather than relying only on final epoch scores.

## Hyperparameter result interpretation

- `all_results` keys are filename-safe strings derived from hyperparameters; parse them for diagnostics but report `best_hyperparams` to users.
- `use_max=True` is correct for AUC, accuracy, R2-like scores, and correlations.
- `use_max=False` is correct for MSE, MAE, RMS, and other losses.
- Candidate model directories may appear in returned random-search params because search methods add `model_dir`; ignore this when comparing scientific settings.

## GBDT pitfalls

- `GBDTModel` requires both XGBoost and LightGBM modules to import.
- `early_stopping_rounds` must be positive.
- Multi-output labels are rejected; reshape to a single task or train separate models.
- Classification uses stratified internal splits; very small or single-class datasets can fail during splitting.
