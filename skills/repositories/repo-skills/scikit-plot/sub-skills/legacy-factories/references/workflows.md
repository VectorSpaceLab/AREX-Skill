# Legacy factories workflows

Use these workflows only when a user must preserve bound-method or deprecated-module code. Prefer direct functions for new code.

## Inject classifier methods

```python
import scikitplot
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier

X, y = load_iris(return_X_y=True)
clf = scikitplot.classifier_factory(RandomForestClassifier(n_estimators=16, random_state=0))
clf.fit(X, y)

ax = clf.plot_confusion_matrix(X, y, do_cv=False)
roc_ax = clf.plot_roc_curve(X, y, do_cv=False)
fi_ax = clf.plot_feature_importances()
```

Use `do_cv=False` only after fitting the classifier. With the default `do_cv=True`, the factory wrapper clones and refits across folds before plotting. Avoid `n_jobs=-1` on factory-injected `plot_learning_curve`; use `n_jobs=1` or migrate to `scikitplot.estimators.plot_learning_curve` if parallelism matters.

## Inject clusterer methods

```python
import scikitplot
from sklearn.cluster import KMeans
from sklearn.datasets import load_iris

X, _ = load_iris(return_X_y=True)
clusterer = scikitplot.clustering_factory(KMeans(n_clusters=3, random_state=0, n_init=10))

elbow_ax = clusterer.plot_elbow_curve(X, cluster_ranges=range(1, 6))
silhouette_ax = clusterer.plot_silhouette(X)
```

Use direct `scikitplot.cluster.plot_elbow_curve` for new elbow-curve code. The factory-injected elbow method comes from the deprecated `plotters` path and does not expose newer options such as `n_jobs` or `show_cluster_time`. Route silhouette calls to `metrics` when you already have cluster labels.

## Migrate deprecated `plotters` imports

| Old import | Preferred route |
| --- | --- |
| `scikitplot.plotters.plot_confusion_matrix` | `scikitplot.metrics.plot_confusion_matrix` |
| `scikitplot.plotters.plot_roc_curve` | `scikitplot.metrics.plot_roc` or legacy `scikitplot.metrics.plot_roc_curve` |
| `scikitplot.plotters.plot_precision_recall_curve` | `scikitplot.metrics.plot_precision_recall` or legacy `scikitplot.metrics.plot_precision_recall_curve` |
| `scikitplot.plotters.plot_feature_importances` | `scikitplot.estimators.plot_feature_importances` |
| `scikitplot.plotters.plot_learning_curve` | `scikitplot.estimators.plot_learning_curve` |
| `scikitplot.plotters.plot_elbow_curve` | `scikitplot.cluster.plot_elbow_curve` |
| `scikitplot.plotters.plot_pca_component_variance` | `scikitplot.decomposition.plot_pca_component_variance` |
| `scikitplot.plotters.plot_pca_2d_projection` | `scikitplot.decomposition.plot_pca_2d_projection` |

## Smoke validation

```bash
python scripts/legacy_factories_smoke.py
```

The helper checks method injection and one representative classifier/clusterer workflow under the Agg backend.
