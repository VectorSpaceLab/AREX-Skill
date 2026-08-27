# KMeans API Reference

Pomegranate includes `KMeans` as a PyTorch-backed clusterer and as an initializer for probabilistic models.

## Constructor signature verified from the package

```python
KMeans(
    k=None,
    centroids=None,
    init='first-k',
    max_iter=10,
    tol=0.1,
    inertia=0.0,
    frozen=False,
    random_state=None,
    verbose=False,
)
```

## Parameters

| Parameter | Meaning |
| --- | --- |
| `k` | Number of clusters. Required unless `centroids` are provided; must be at least 2. |
| `centroids` | Explicit initial centroid matrix shaped `(k, d)`. |
| `init` | Initialization when centroids are absent: `'first-k'`, `'random'`, `'submodular-facility-location'`, or `'submodular-feature-based'`. |
| `max_iter` | Maximum update iterations. |
| `tol` | Convergence threshold. |
| `inertia` | Update interpolation; `1.0` keeps old centroids. |
| `frozen` | Prevents centroid updates. |
| `random_state` | Determinism for random/submodular initializers. |
| `verbose` | Print improvements and timing during fitting. |

## Methods

| Method | Use |
| --- | --- |
| `fit(X, sample_weight=None)` | Learn centroids. |
| `predict(X)` | Assign each example to the nearest centroid. |
| `fit_predict(X, sample_weight=None)` | Fit and return assignments. |
| `summarize(X, sample_weight=None)` | Accumulate centroid sufficient statistics. |
| `from_summaries()` | Update centroids from accumulated statistics. |

## Basic recipe

```python
import torch
from pomegranate.kmeans import KMeans

X = torch.tensor([[0.0, 0.0], [0.0, 1.0], [5.0, 5.0], [5.0, 6.0]])
model = KMeans(k=2, init="first-k", max_iter=10, tol=1e-4)
labels = model.fit_predict(X)
centroids = model.centroids
```

## Weighted update recipe

```python
weights = torch.tensor([1.0, 1.0, 2.0, 2.0])
model = KMeans(k=2, init="first-k")
model.fit(X, sample_weight=weights)
```

## Initialization choices

- Use `first-k` for deterministic smoke checks and debugging.
- Use `random` with `random_state` for ordinary randomized initialization.
- Use `submodular-facility-location` or `submodular-feature-based` only when the dependency stack includes `apricot-select` and the dataset warrants more sophisticated seeding.

## Relationship to mixture models

`GeneralMixtureModel` uses KMeans-style initialization when component distributions are not already initialized. If a mixture model converges poorly, reproduce the issue with `KMeans` on the same feature matrix to check whether centroid initialization is the main cause.
