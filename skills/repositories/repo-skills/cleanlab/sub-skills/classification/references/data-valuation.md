# Data valuation

`data_shapley_knn` is the main classification-support helper for estimating how much each data point helps a classifier.
It is useful when the user wants to keep, drop, or inspect examples by contribution rather than by label quality.

## Public API

```python
data_shapley_knn(
    labels,
    *,
    features=None,
    knn_graph=None,
    metric=None,
    k=10,
)
```

Input rules:

- `labels` are for a standard multiclass classification dataset.
- provide either `features` or `knn_graph`
- `features` must be 2D when supplied
- `k` must be less than the number of examples
- if `knn_graph` is supplied, it should already match the same example order as `labels`

Output:

- an array of transformed Data Shapley scores in `[0, 1]`
- values above `0.5` suggest positive contribution
- values below `0.5` suggest a point that may hurt the learner

## Preferred usage patterns

### From features

Use this when you just have a feature matrix.

```python
import numpy as np
from cleanlab.data_valuation import data_shapley_knn

labels = np.array([0, 1, 0, 1, 0])
features = np.array(
    [
        [0.0, 0.0],
        [0.0, 1.0],
        [1.0, 0.0],
        [1.0, 1.0],
        [0.2, 0.2],
    ],
    dtype=float,
)
scores = data_shapley_knn(labels=labels, features=features, k=3)
```

### From a precomputed KNN graph

Use this when you already have nearest neighbors or want to reuse them across workflows.

```python
from sklearn.neighbors import NearestNeighbors
from cleanlab.data_valuation import data_shapley_knn

knn_graph = NearestNeighbors(n_neighbors=3).fit(features).kneighbors_graph(mode="distance")
scores = data_shapley_knn(labels=labels, knn_graph=knn_graph, k=3)
```

## Troubleshooting

- If the call fails, check that either `features` or `knn_graph` is present.
- If `k` is too large, reduce it so it stays below the number of examples.
- If the labels are multi-label or otherwise not single-class integers, route to the task-specific sub-skill instead.
- If the user wants a better notion of per-example label quality rather than contribution, route back to the core classification workflow instead of data valuation.
