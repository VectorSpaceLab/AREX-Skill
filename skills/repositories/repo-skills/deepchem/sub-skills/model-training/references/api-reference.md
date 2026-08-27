# Model, Metric, and Hyperparameter API Reference

## Core model lifecycle

DeepChem model wrappers expose a shared lifecycle on `dc.data.Dataset` objects:

```python
model.fit(train_dataset)
scores = model.evaluate(valid_dataset, [metric], transformers=[])
predictions = model.predict(test_dataset, transformers=[])
model.save()
```

`Model.evaluate(dataset, metrics, transformers=[], per_task_metrics=False, use_sample_weights=False, n_classes=2)` returns a dictionary keyed by each `Metric.name`. If `per_task_metrics=True`, it returns an additional per-task score mapping. Use `transformers` when labels were transformed and scores must be computed on the original scale.

## Base wrappers

### `SklearnModel`

Signature: `dc.models.SklearnModel(model, model_dir=None, **kwargs)`.

Use it to wrap a scikit-learn estimator so it trains on DeepChem datasets and evaluates with DeepChem metrics.

```python
from sklearn.ensemble import RandomForestRegressor
import deepchem as dc

sk_model = RandomForestRegressor(n_estimators=32, random_state=0)
model = dc.models.SklearnModel(sk_model, model_dir="./dc-rf-model")
model.fit(train_dataset)
metric = dc.metrics.Metric(dc.metrics.pearson_r2_score)
scores = model.evaluate(valid_dataset, [metric])
preds = model.predict(valid_dataset)
model.save()
```

Important behavior:
- `fit()` uses `dataset.X`, squeezed `dataset.y`, and squeezed `dataset.w`.
- If the wrapped estimator supports `predict_proba()`, predictions use probabilities; otherwise they use `predict()`.
- `save()` writes the estimator under `model_dir`; reloading is done by creating `dc.models.SklearnModel(None, model_dir=same_dir)` and calling `reload()`.
- Pass `use_weights=False` if the estimator cannot accept sample weights and automatic detection is not enough.

### `GBDTModel`

Signature: `dc.models.GBDTModel(model, model_dir=None, early_stopping_rounds=50, eval_metric=None, **kwargs)`.

Use it only when LightGBM and XGBoost are installed. The wrapped estimator class name must look like an XGBoost or LightGBM classifier/regressor. It supports single-output tasks only.

```python
import deepchem as dc
from xgboost import XGBRegressor

gbdt = dc.models.GBDTModel(
    XGBRegressor(n_estimators=100, random_state=0),
    model_dir="./dc-gbdt-model",
    early_stopping_rounds=10,
    eval_metric="mae",
)
gbdt.fit(train_dataset)
```

`GBDTModel.fit()` internally splits training data into train/validation for early stopping, then retrains with a tuned number of estimators. Use `fit_with_eval(train_dataset, valid_dataset)` when you already have a validation set.

## Metrics

Signature: `dc.metrics.Metric(metric, task_averager=None, name=None, threshold=None, mode=None, n_tasks=None, classification_handling_mode=None, threshold_value=None)`.

Common metrics:
- Regression: `pearson_r2_score`, `r2_score`, `mean_squared_error`, `mean_absolute_error`, `rms_score`, `mae_score`, `pearsonr`, `concordance_index`.
- Classification: `roc_auc_score`, `prc_auc_score`, `accuracy_score`, `balanced_accuracy_score`, `matthews_corrcoef`, `recall_score`, `precision_score`, `f1_score`.

Examples:

```python
regression_metric = dc.metrics.Metric(dc.metrics.pearson_r2_score)
loss_metric = dc.metrics.Metric(dc.metrics.mean_squared_error, mode="regression")
auc_metric = dc.metrics.Metric(dc.metrics.roc_auc_score, mode="classification")
accuracy_metric = dc.metrics.Metric(
    dc.metrics.accuracy_score,
    mode="classification",
    classification_handling_mode="threshold",
)
```

Shape rules:
- Regression labels: `(N,)`, `(N, n_tasks)`, or `(N, n_tasks, 1)`.
- Regression predictions: usually `(N,)` or `(N, n_tasks)`.
- Classification labels: `(N,)`, `(N, n_tasks)`, or `(N, n_tasks, n_classes)`.
- Classification predictions: preferably `(N, n_tasks, n_classes)` probabilities, especially for ROC-AUC/PRC-AUC.
- Weights, when used, should normalize to `(N, n_tasks)`.

Classification handling modes:
- `direct`: pass normalized labels/predictions directly to the metric; default for ROC-AUC and PRC-AUC.
- `threshold`: convert probabilities to class indices; useful for F1, recall, Matthews correlation, balanced accuracy.
- `threshold-one-hot`: threshold then one-hot encode; default for some accuracy/precision paths.

## Hyperparameter search

Construct an optimizer around a builder that returns a DeepChem model. Search calls train candidate models and evaluate on the validation set.

```python
import deepchem as dc
from sklearn.ensemble import RandomForestRegressor

def model_builder(n_estimators=32, max_depth=None, model_dir=None):
    estimator = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=0,
    )
    return dc.models.SklearnModel(estimator, model_dir=model_dir)

params = {"n_estimators": [16, 32], "max_depth": [None, 4]}
metric = dc.metrics.Metric(dc.metrics.pearson_r2_score)
optimizer = dc.hyper.GridHyperparamOpt(model_builder)
best_model, best_hyperparams, all_scores = optimizer.hyperparam_search(
    params, train_dataset, valid_dataset, metric, use_max=True, logdir="./dc-hparam"
)
```

Signatures:
- `dc.hyper.GridHyperparamOpt(model_builder)` tries every iterable combination in `params_dict`.
- `dc.hyper.RandomHyperparamOpt(model_builder, max_iter)` samples `max_iter` combinations; values may be iterables or callables such as `scipy.stats` `.rvs` methods.
- `hyperparam_search(params_dict, train_dataset, valid_dataset, metric, output_transformers=[], nb_epoch=10, use_max=True, logfile='results.txt', logdir=None, **kwargs)` returns `(best_model, best_hyperparams, all_scores)`.

Set `use_max=False` for losses such as mean squared error or mean absolute error.
