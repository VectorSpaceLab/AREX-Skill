# API Reference: Clustering

Use these imports when working in this sub-skill:

```python
from tslearn.clustering import (
    EmptyClusterError,
    KShape,
    KernelKMeans,
    TimeSeriesDBSCAN,
    TimeSeriesKMeans,
    silhouette_score,
)
```

## Verified constructor signatures

- `TimeSeriesKMeans(n_clusters=3, max_iter=50, tol=1e-06, n_init=1, metric='euclidean', max_iter_barycenter=100, metric_params=None, n_jobs=None, dtw_inertia=False, verbose=0, random_state=None, init='k-means++')`
- `KernelKMeans(n_clusters=3, kernel='gak', max_iter=50, tol=1e-06, n_init=1, kernel_params=None, n_jobs=None, verbose=0, random_state=None)`
- `KShape(n_clusters=3, max_iter=100, tol=1e-06, n_init=1, verbose=False, random_state=None, init='random')`
- `TimeSeriesDBSCAN(eps=0.5, min_ts=5, metric='dtw', metric_params=None, n_jobs=None)`
- `silhouette_score(X, labels, metric=None, sample_size=None, metric_params=None, n_jobs=None, verbose=0, random_state=None, **kwds)`

## Centroid and label contract

| Estimator | Centroids? | Prediction | Variable-length input | Main outputs |
| --- | --- | --- | --- | --- |
| `TimeSeriesKMeans` | Yes, `cluster_centers_` | `fit_predict`, `predict`, `transform` | Yes for `metric="dtw"` and `metric="softdtw"`; no for `metric="euclidean"` | `labels_`, `cluster_centers_`, `inertia_`, `n_iter_` |
| `KernelKMeans` | No explicit centroid | `fit_predict`, `predict` | Yes with GAK; other kernels follow `pairwise_kernels` input rules | `labels_`, `inertia_`, `sample_weight_`, `n_iter_`, `_X_fit` |
| `KShape` | Yes, `cluster_centers_` | `fit_predict`, `predict` | No; expects equal-length, scaled series | `labels_`, `cluster_centers_`, `inertia_`, `n_iter_` |
| `TimeSeriesDBSCAN` | No centroids | `fit`, `fit_predict` | Yes for `dtw`, `ctw`, `frechet`, and `softdtw_normalized`; no for `euclidean` and `precomputed` | `labels_`, `components_`, `core_ts_indices_` |
| `silhouette_score` | N/A | N/A | Yes when the chosen metric supports it | Scalar score |

## Utility notes

- `EmptyClusterError` marks an empty-cluster failure.
- `TimeSeriesCentroidBasedClusteringMixin` is shared centroid logic used by the centroid-based estimators.
- `TimeSeriesDBSCAN` uses `-1` for noise labels and stores core samples in `components_`.

## TimeSeriesKMeans details

- `metric="euclidean"` uses pointwise means as centroids.
- `metric="dtw"` uses DTW barycenters (DBA).
- `metric="softdtw"` uses Soft-DTW barycenters.
- `dtw_inertia=True` computes DTW inertia even when another metric is used.
- `init` accepts `"k-means++"`, `"random"`, or an array of initial centroids.
- `transform(X)` returns distances from each sample to each centroid.
- `predict(X)` returns the nearest centroid index for each sample.

## KernelKMeans details

- The default kernel is `"gak"`.
- `kernel_params` may include `sigma` for GAK or parameters for another `pairwise_kernels` metric.
- Tiny datasets can make `sigma="auto"` collapse to zero; use an explicit positive `sigma` when needed.
- There is no `cluster_centers_` attribute because kernel k-means does not form explicit centroids.

## KShape details

- Normalize each series before fit; the common path is `TimeSeriesScalerMeanVariance(mu=0., std=1.)`.
- `init` must be `"random"` or an array with one initial centroid per cluster.
- KShape is shape-based: it clusters normalized series, not raw amplitude scale.

## TimeSeriesDBSCAN details

- Verified `metric` values are `"dtw"`, `"ctw"`, `"frechet"`, `"softdtw_normalized"`, `"euclidean"`, and `"precomputed"`.
- `metric_params` are filtered to the chosen metric signature.
- `n_jobs` in `metric_params` is overridden by the estimator's `n_jobs` argument.
- `fit_predict` returns labels with `-1` for noise; there is no out-of-sample `predict`.
- `components_` is empty when no core samples are found.

## silhouette_score details

- `metric=None` defaults to DTW.
- `metric="dtw"` and `metric="softdtw"` build a time-series distance matrix internally.
- `metric="softdtw"` uses the normalized Soft-DTW form.
- `metric="euclidean"` flattens the series before scoring.
- `metric="precomputed"` expects a square distance matrix in the same sample order as `labels`.
- `sample_size` and `random_state` behave like the scikit-learn silhouette implementation.

For recipes, see [workflows.md](workflows.md). For failure handling, see [troubleshooting.md](troubleshooting.md).
