# Workflows: Clustering

Use these workflows for tslearn clustering on tiny synthetic data, small curated datasets, or preprocessed time-series batches.

## 1. Tiny dataset to fit, predict, and silhouette

Use a tiny dataset first so that centroid behavior and score calculations are easy to inspect.

```python
from tslearn.clustering import TimeSeriesKMeans, silhouette_score
from tslearn.metrics import cdist_dtw
from tslearn.utils import to_time_series_dataset

X = to_time_series_dataset([
    [0., 0., 1., 0.],
    [0., 1., 0., 0.],
    [1., 1., 0., 1.],
    [1., 0., 1., 1.],
    [0., 0., 0., 1.],
    [1., 0., 0., 0.],
])

km = TimeSeriesKMeans(
    n_clusters=2,
    metric="dtw",
    random_state=0,
    n_init=2,
    max_iter=5,
    max_iter_barycenter=5,
)
labels = km.fit_predict(X)
pred = km.predict(X)
assert (pred == labels).all()
print(km.cluster_centers_.shape)

score = silhouette_score(X, labels, metric="dtw")
score_pre = silhouette_score(cdist_dtw(X), labels, metric="precomputed")
assert abs(score - score_pre) < 1e-9
print(score)
```

If you want to compare geometries on the same dataset, fit a second `TimeSeriesKMeans` with `metric="euclidean"` and compare both the labels and the silhouette scores.

## 2. KShape needs normalized, equal-length input

KShape is a shape-based algorithm. Scale first, then fit.

```python
from tslearn.clustering import KShape
from tslearn.preprocessing import TimeSeriesScalerMeanVariance

X_scaled = TimeSeriesScalerMeanVariance(mu=0., std=1.).fit_transform(X)
ks = KShape(n_clusters=2, random_state=0, n_init=2)
labels = ks.fit_predict(X_scaled)
assert (ks.predict(X_scaled) == labels).all()
print(ks.cluster_centers_.shape)
```

Use this path when the raw amplitude scale is not meaningful and you want normalized shape clusters.

## 3. No-centroid workflows

### Kernel k-means

```python
from tslearn.clustering import KernelKMeans

kk = KernelKMeans(
    n_clusters=2,
    kernel="gak",
    kernel_params={"sigma": 1.0},
    random_state=0,
    n_init=2,
    max_iter=5,
)
labels = kk.fit_predict(X)
assert (kk.predict(X) == labels).all()
```

There is no `cluster_centers_` here. Treat the result as assignments only.

### DBSCAN

```python
from tslearn.clustering import TimeSeriesDBSCAN

db = TimeSeriesDBSCAN(eps=0.5, min_ts=2, metric="dtw")
labels = db.fit_predict(X)
print(db.core_ts_indices_)
print(db.components_.shape)
```

`TimeSeriesDBSCAN` is fit-only. Use `labels_`, `components_`, and `core_ts_indices_` instead of centroids.

## 4. Variable-length workflow

Convert ragged lists with `to_time_series_dataset(...)`, then choose a metric that supports ragged input.

```python
X_var = to_time_series_dataset([
    [0., 0., 1., 0.],
    [0., 1., 0.],
    [1., 1., 0., 1., 0.],
    [1., 0., 1.],
    [0., 0., 0., 1.],
    [1., 0., 0.],
])

km = TimeSeriesKMeans(
    n_clusters=2,
    metric="softdtw",
    metric_params={"gamma": 0.1},
    random_state=0,
    n_init=2,
    max_iter=5,
    max_iter_barycenter=5,
)
labels = km.fit_predict(X_var)
assert (km.predict(X_var) == labels).all()
print(km.cluster_centers_.shape)
```

For ragged input, prefer DTW or Soft-DTW KMeans, GAK kernel k-means, or DBSCAN with a supported metric. If you need Euclidean KMeans or KShape, route to [data-preparation](../../data-preparation/) and resample first.

## 5. Recover from brittle runs

- Empty-cluster behavior: lower `n_clusters`, raise `n_init`, or provide a better `init`.
- GAK collapse on tiny data: use an explicit positive `sigma` instead of `sigma="auto"`.
- Metric mismatch: do not mix ragged input with Euclidean or KShape unless you resample first.
- Random-state sensitivity: fix `random_state` and compare the same dataset under multiple metrics before changing the data.

For implementation details, see [api-reference.md](api-reference.md). For failure-specific checks, see [troubleshooting.md](troubleshooting.md).
