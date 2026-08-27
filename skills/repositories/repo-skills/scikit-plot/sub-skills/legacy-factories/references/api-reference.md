# Legacy factories API reference

Source anchors: `scikitplot/classifiers.py`, `scikitplot/clustering.py`, `scikitplot/plotters.py`, `docs/apidocs.rst`, `docs/functionsapidocs.rst`, and the factory/plotters tests.

## `classifier_factory`

```python
classifier_factory(clf) -> clf
```

Verified behavior:

- Requires `fit`, `score`, and `predict` on `clf`; otherwise raises `TypeError`.
- Warns when `predict_proba` is absent because probability-based plots may fail later.
- Injects bound methods into the same classifier object and returns it.
- Warns when an injected method name already exists, then overrides it.
- Marked deprecated in source comments and warnings; direct functions are preferred for new code.

Injected classifier methods:

| Injected method | Underlying route | Notes |
| --- | --- | --- |
| `plot_learning_curve` | `estimators` | wraps `plot_learning_curve(clf, X, y, ...)`; prefer `n_jobs=1` on injected methods because joblib parallel workers may fail to pickle method-injected estimators |
| `plot_confusion_matrix` | `metrics` | can cross-validate or use `do_cv=False` on a fitted model |
| `plot_roc_curve` | `metrics` legacy ROC API | needs `predict_proba` |
| `plot_ks_statistic` | `metrics` | needs binary labels and `predict_proba` |
| `plot_precision_recall_curve` | `metrics` legacy PR API | needs `predict_proba` |
| `plot_feature_importances` | `estimators` | needs `feature_importances_` on the fitted estimator |

## `clustering_factory`

```python
clustering_factory(clf) -> clf
```

Verified behavior:

- Requires `fit` and `fit_predict`; otherwise raises `TypeError`.
- Injects bound methods into the same clusterer object and returns it.
- Warns when an injected method name already exists, then overrides it.
- Marked deprecated in source comments and warnings; direct functions are preferred for new code.

Injected clusterer methods:

| Injected method | Underlying route | Notes |
| --- | --- | --- |
| `plot_silhouette` | legacy `plotters` compatibility | fits or uses the clusterer to produce cluster labels |
| `plot_elbow_curve` | deprecated `plotters` compatibility; use `clustering` for new code | needs `n_clusters`, cloneability, `fit`, and `score`; the injected method does not accept newer direct-function options such as `n_jobs` or `show_cluster_time` |

## Deprecated `scikitplot.plotters`

`scikitplot.plotters` imports with a deprecation warning and exposes older names for metric, estimator, cluster, and PCA functions. Treat it as a compatibility layer only. For new code, import from `scikitplot.metrics`, `scikitplot.estimators`, `scikitplot.cluster`, or `scikitplot.decomposition`.
