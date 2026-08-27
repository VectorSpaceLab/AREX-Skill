# Unsupervised and reduction API reference

## Purpose

Read this when a task needs exact import paths, constructor defaults, outputs, state attributes, or compatibility notes for MLAlgorithms clustering, reduction, RBM, distances, metrics, and demo data loaders.

## Shared unsupervised pattern

`KMeans`, `GaussianMixture`, `PCA`, `TSNE`, and `RBM` either inherit `BaseEstimator` with `y_required = False` or expose unsupervised methods directly. They still expect non-empty NumPy-compatible feature arrays. Use 2D arrays for tabular data and keep plotting optional.

## Clustering

```python
from mla.kmeans import KMeans
from mla.gaussian_mixture import GaussianMixture
```

| Object | Signature | Output/state | Notes |
| --- | --- | --- | --- |
| `KMeans` | `KMeans(K=5, max_iters=100, init='random')` | `predict()` returns cluster ids for the fitted training data; stores `clusters` and `centroids` | `init` is `"random"` or `"++"`. `plot()` is only useful for 2D data and may open a display. |
| `GaussianMixture` | `GaussianMixture(K=4, init='random', max_iters=500, tolerance=0.001)` | `predict(X)` returns assignment ids; stores `weights`, `means`, `covs`, `responsibilities`, `likelihood` | `init` is `"random"` or `"kmeans"`. Uses SciPy multivariate normal density and full covariance matrices. |

`KMeans.fit(X)` stores the dataset. `KMeans.predict()` does not need an argument for the fitted data. `GaussianMixture.predict(X)` accepts new data and can also use fitted assignments internally.

## Dimensionality reduction

```python
from mla.pca import PCA
from mla.tsne import TSNE
```

| Object | Signature | Output/state | Notes |
| --- | --- | --- | --- |
| `PCA` | `PCA(n_components, solver='svd')` | `transform(X)` returns `(n_samples, n_components)`; stores `mean` and `components` | `solver` is `"svd"` or `"eigen"`. Fit on training data, transform train/test separately. |
| `TSNE` | `TSNE(n_components=2, perplexity=30.0, max_iter=200, learning_rate=500)` | `fit_transform(X)` returns embedding array | Dense pairwise distances and Python loops make this slow for large `n_samples`. |

`PCA._predict(X)` delegates to `transform(X)`, so `predict(X)` is also available after fitting. Prefer explicit `transform` for clarity.

## RBM

```python
from mla.rbm import RBM
```

`RBM(n_hidden=128, learning_rate=0.1, batch_size=10, max_epochs=100)` implements a Bernoulli restricted Boltzmann machine with CD-1 style training. `fit(X)` initializes weights and stores per-epoch reconstruction errors in `errors`. `predict(X)` returns hidden-unit probabilities with shape `(n_samples, n_hidden)`.

Inputs should be binary or scaled into `[0, 1]`. Use small `max_epochs` for smoke tests.

## Dataset loaders

```python
from mla.datasets import load_mnist, load_nietzsche
```

| Loader | Return value | Notes |
| --- | --- | --- |
| `load_mnist()` | `(X_train, X_test, y_train, y_test)` | Reads packaged IDX files, reshapes images to `(n, 1, 28, 28)`, and casts images to `float32`. Intended by the ConvNet recipe. |
| `load_nietzsche()` | `(X, y, text, chars, char_indices, indices_char)` | Creates one-hot character sequences of length 40 from packaged text data. In version `0.0.1`, source uses deprecated `np.bool`; NumPy versions before 1.24 avoid that failure. |

The generated skill does not copy demo datasets. Use loaders from an installed package when needed.

## Metrics and distances used by these workflows

```python
from mla.metrics.distance import euclidean_distance, l2_distance
from mla.metrics.metrics import accuracy, mean_squared_error, get_metric
```

- `euclidean_distance(a, b)` computes scalar Euclidean distance and accepts lists or arrays.
- `l2_distance(X)` computes a dense pairwise squared-distance-like matrix used by t-SNE.
- `get_metric(name)` returns a metric function by global name or raises `ValueError("Invalid metric function.")`.

See the root API reference for the full metric list.
