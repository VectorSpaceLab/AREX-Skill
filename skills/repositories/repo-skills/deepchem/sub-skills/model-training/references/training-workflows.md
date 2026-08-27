# Training Workflows

## Fast sklearn baseline

Use this workflow for minimal environments, tabular descriptors/fingerprints, smoke tests, and baseline comparisons.

```python
import deepchem as dc
from sklearn.ensemble import RandomForestRegressor

model = dc.models.SklearnModel(
    RandomForestRegressor(n_estimators=64, random_state=0),
    model_dir="./rf-baseline",
)
model.fit(train_dataset)
metric = dc.metrics.Metric(dc.metrics.pearson_r2_score)
valid_scores = model.evaluate(valid_dataset, [metric])
test_predictions = model.predict(test_dataset)
model.save()
```

For classification baselines, choose an estimator with `predict_proba()` if using `roc_auc_score` or `prc_auc_score`.

```python
from sklearn.ensemble import RandomForestClassifier

model = dc.models.SklearnModel(RandomForestClassifier(random_state=0))
metric = dc.metrics.Metric(dc.metrics.roc_auc_score, mode="classification")
```

## Metric selection checklist

- Regression target: start with `pearson_r2_score` or `mean_absolute_error`; set `use_max=False` for losses in hyperparameter search.
- Binary/multitask classification: start with `roc_auc_score` if predictions are probabilities; use `np.mean` or another task averager for multi-task reporting if desired.
- Thresholded classification reports: use `accuracy_score`, `f1_score`, or `matthews_corrcoef` with `classification_handling_mode="threshold"` when class labels are needed.
- Transformed labels: pass the same output transformers to `evaluate()` or `hyperparam_search(..., output_transformers=transformers)`.
- Multi-task debugging: call `evaluate(..., per_task_metrics=True)` to inspect task-level failures instead of relying only on averaged scores.

## Save, reload, and restore

### Scikit-learn wrappers

```python
model = dc.models.SklearnModel(estimator, model_dir="./saved-sklearn")
model.fit(train_dataset)
model.save()

reloaded = dc.models.SklearnModel(None, model_dir="./saved-sklearn")
reloaded.reload()
preds = reloaded.predict(test_dataset)
```

### Neural wrappers

Neural wrappers such as `TorchModel` and `KerasModel` generally use checkpoints rather than a joblib estimator file.

```python
model.fit(train_dataset, nb_epoch=5)
model.save_checkpoint()

same_model = build_same_architecture(model_dir="./checkpoint-dir")
same_model.restore()
```

For best-validation checkpoints in `KerasModel`, use `dc.models.ValidationCallback(valid_dataset, interval, metrics, save_dir=...)` and restore from the saved directory after training.

## Hyperparameter search

Use a builder that accepts candidate parameters plus `model_dir` and returns a fresh DeepChem model.

```python
import deepchem as dc
from sklearn.ensemble import RandomForestRegressor

def build_rf(n_estimators=32, max_features=1.0, model_dir=None):
    return dc.models.SklearnModel(
        RandomForestRegressor(
            n_estimators=n_estimators,
            max_features=max_features,
            random_state=0,
        ),
        model_dir=model_dir,
    )

params = {"n_estimators": [16, 64], "max_features": [0.5, 1.0]}
metric = dc.metrics.Metric(dc.metrics.mean_absolute_error, mode="regression")
optimizer = dc.hyper.GridHyperparamOpt(build_rf)
best_model, best_params, all_results = optimizer.hyperparam_search(
    params,
    train_dataset,
    valid_dataset,
    metric,
    use_max=False,
    logdir="./search-runs",
)
```

Interpretation notes:
- `best_params` excludes the generated `model_dir` for grid search but random search may include it in returned dictionaries depending on mutation during fitting; ignore `model_dir` when reporting scientific hyperparameters.
- `all_results` maps filename-safe hyperparameter strings to validation scores.
- Searches are serial; keep grids small for expensive neural models.
- `nb_epoch` is passed to model `fit()` when supported, and retried without it for models such as `SklearnModel`.

## Optional neural model workflow

Use this only when the required backend is installed.

1. Choose featurization first: graph models require graph featurizers, image models require image featurizers, sequence models require token/sequence featurizers.
2. Import the model class inside a dependency check so missing extras fail with a clear message.
3. Construct with `n_tasks`, `mode`, `batch_size`, `learning_rate`, and `model_dir` as appropriate.
4. Fit with `nb_epoch`, evaluate with metrics that match `mode`, then checkpoint or restore.

```python
try:
    import torch  # noqa: F401
except ImportError as exc:
    raise RuntimeError("Install DeepChem with the PyTorch extras before using Torch-backed models.") from exc

import deepchem as dc

model = dc.models.MultitaskClassifier(
    n_tasks=n_tasks,
    n_features=n_features,
    layer_sizes=[512],
    dropouts=[0.2],
    model_dir="./torch-multitask",
)
metric = dc.metrics.Metric(dc.metrics.roc_auc_score, mode="classification")
model.fit(train_dataset, nb_epoch=10)
scores = model.evaluate(valid_dataset, [metric])
model.save_checkpoint()
```

If the import itself emits TensorFlow, PyTorch, JAX, DGL, or PyTorch Geometric warnings, do not debug model code first; confirm the optional backend stack is installed and compatible.
