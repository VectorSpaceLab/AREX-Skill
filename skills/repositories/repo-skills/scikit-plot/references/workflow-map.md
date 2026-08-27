# scikit-plot workflow map

Use this map when a request names a plot type, data shape, or compatibility surface but not the exact sub-skill.

| Route | Primary functions | Trigger terms | Key inputs | Bundled smoke |
| --- | --- | --- | --- | --- |
| `metrics` | `plot_confusion_matrix`, `plot_roc`, `plot_precision_recall`, `plot_ks_statistic`, `plot_calibration_curve`, `plot_cumulative_gain`, `plot_lift_curve`, `plot_silhouette` | confusion matrix, ROC, PR, KS, calibration, lift, gain, silhouette | labels, predictions, probability matrices, cluster labels | `sub-skills/metrics/scripts/metrics_smoke.py` |
| `estimators` | `plot_feature_importances`, `plot_learning_curve` | feature importance, learning curve, estimator diagnostics | fitted estimator, feature names, CV/scoring options | `sub-skills/estimators/scripts/estimators_smoke.py` |
| `clustering` | `plot_elbow_curve` | elbow curve, choose K, cluster count sweep | cloneable clusterer with `n_clusters`, data matrix | `sub-skills/clustering/scripts/clustering_smoke.py` |
| `decomposition` | `plot_pca_component_variance`, `plot_pca_2d_projection` | PCA variance, PCA projection, biplot | fitted PCA-like object, `X`, labels, optional feature labels | `sub-skills/decomposition/scripts/decomposition_smoke.py` |
| `legacy-factories` | `classifier_factory`, `clustering_factory`, deprecated `scikitplot.plotters` module | old bound-method code, factory injection, deprecated plotters imports | classifier or clusterer objects with expected methods | `sub-skills/legacy-factories/scripts/legacy_factories_smoke.py` |

## Boundary notes

- `plot_silhouette` belongs to `metrics` because it consumes `X` and cluster labels as a metric-style diagnostic.
- `plot_elbow_curve` belongs to `clustering` because it refits a clusterer across candidate `n_clusters` values.
- Factory-generated bound methods belong to `legacy-factories`, even when the wrapped plot ultimately comes from `metrics`, `estimators`, or `clustering`.
- The deprecated `scikitplot.plotters` module is compatibility evidence, not the preferred new route.
