# Core UMAP API Reference

This reference is for public package `umap-learn` 0.5.12, imported as `umap`, on Python 3.10+. It covers the base non-parametric `umap.UMAP` estimator only.

## Imports

```python
import umap
from umap.umap_ import UMAP, nearest_neighbors, find_ab_params
```

Use `umap.UMAP` or `from umap import UMAP` for ordinary estimator work. Importing from `umap.umap_` is useful for helper functions such as `nearest_neighbors` when constructing `precomputed_knn`.

## Verified constructor signature

```python
umap.UMAP(
    n_neighbors=15,
    n_components=2,
    metric='euclidean',
    metric_kwds=None,
    output_metric='euclidean',
    output_metric_kwds=None,
    n_epochs=None,
    learning_rate=1.0,
    init='spectral',
    min_dist=0.1,
    spread=1.0,
    low_memory=True,
    n_jobs=-1,
    set_op_mix_ratio=1.0,
    local_connectivity=1.0,
    repulsion_strength=1.0,
    negative_sample_rate=5,
    transform_queue_size=4.0,
    a=None,
    b=None,
    random_state=None,
    angular_rp_forest=False,
    target_n_neighbors=-1,
    target_metric='categorical',
    target_metric_kwds=None,
    target_weight=0.5,
    transform_seed=42,
    transform_mode='embedding',
    force_approximation_algorithm=False,
    verbose=False,
    tqdm_kwds=None,
    unique=False,
    densmap=False,
    dens_lambda=2.0,
    dens_frac=0.3,
    dens_var_shift=0.1,
    output_dens=False,
    disconnection_distance=None,
    precomputed_knn=(None, None, None),
)
```

### Core constructor parameters

| Parameter | Use it for | Important behavior |
| --- | --- | --- |
| `n_neighbors` | Local/global manifold trade-off. | Must be greater than 1. Values around 5-15 emphasize local detail; larger values emphasize broader/global structure. If it exceeds the effective sample count, UMAP warns and truncates to `X.shape[0] - 1`. |
| `n_components` | Output dimensionality. | Must be a positive integer. `2` is common for visualization; larger values such as 10-50 can be useful as ML features. |
| `metric` | Distance in the original input space. | String metric or callable. `metric='precomputed'` changes `X` semantics to a distance matrix. Callable metrics should be numba-JIT compatible for performance. |
| `metric_kwds` | Extra metric arguments. | Used for metrics such as `minkowski`, `mahalanobis`, and custom metrics. Preserve keyword order when the metric depends on ordered values. |
| `output_metric` | Distance in the embedding space. | Defaults to `euclidean`. Non-Euclidean output metrics need gradients; `output_metric='precomputed'` is invalid. |
| `min_dist` and `spread` | How tightly points can pack in the embedding. | `min_dist` must be non-negative and not greater than `spread`. Smaller `min_dist` makes tighter clusters; larger values produce more even spacing. |
| `random_state` | Reproducible fitting. | Setting it gives repeatable layouts, but UMAP overrides effective `n_jobs` to `1` and warns because parallel optimization is not fully reproducible. |
| `n_jobs` | Number of numba threads for supported phases. | Must be `-1` or a positive integer. `0` and values below `-1` raise `ValueError`. Ignored/overridden to `1` when `random_state` is set. |
| `low_memory` | Lower-memory neighbor search. | Default is `True` in 0.5.12. It can reduce memory at the cost of speed. |
| `force_approximation_algorithm` | Use approximate neighbor path even for smaller data. | Useful to exercise the same approximate path as larger datasets or to keep transform/search-index behavior consistent. It is irrelevant when an accepted `precomputed_knn` is supplied. |
| `transform_seed` | Reproducible `transform` initialization. | Controls stochastic transform of new data; it does not replace `random_state` for the fitted training layout. |
| `transform_mode` | Return embedding or graph from transform calls. | Default `embedding`. `graph` makes `fit_transform`/`transform` return sparse graph matrices instead of coordinates and disables `inverse_transform`. |
| `unique` | Collapse duplicate rows before embedding. | Helpful when duplicates exceed `n_neighbors`; exposes `_unique_inverse_` to map internal unique rows back. Invalid with `metric='precomputed'`. |
| `disconnection_distance` | Remove too-distant edges from the neighbor graph. | Defaults to metric-specific maxima for bounded metrics and `inf` otherwise. Disconnected vertices receive `NaN` embedding coordinates. |
| `precomputed_knn` | Reuse a k-nearest-neighbor graph. | Tuple of `(knn_indices, knn_dists, knn_search_index)` or `(knn_indices, knn_dists)`. See [Precomputed k-NN](#precomputed-k-nn). |

### Route-only parameters in this sub-skill

The constructor also has supervised and density parameters (`target_n_neighbors`, `target_metric`, `target_metric_kwds`, `target_weight`, `densmap`, `dens_lambda`, `dens_frac`, `dens_var_shift`, `output_dens`). Route tasks focused on these to `../../supervised-density/SKILL.md`. This sub-skill only notes their interactions when they block core methods, such as `densmap=True` disabling `transform` and `inverse_transform`.

## Verified method signatures

```python
UMAP.fit(self, X, y=None, ensure_all_finite=True, **kwargs)
UMAP.fit_transform(self, X, y=None, ensure_all_finite=True, **kwargs)
UMAP.transform(self, X, ensure_all_finite=True)
UMAP.inverse_transform(self, X)
UMAP.update(self, X, ensure_all_finite=True)
```

### `fit(X, y=None, ensure_all_finite=True, **kwargs)`

Fits the estimator and returns `self`.

- Ordinary `X`: array-like or `scipy.sparse` matrix with shape `(n_samples, n_features)`.
- `metric='precomputed'`: `X` is a square distance matrix with shape `(n_samples, n_samples)`.
- `ensure_all_finite=True`: reject `NaN`, `inf`, and pandas missing values. Use `False` to accept all non-finite values or `'allow-nan'` to accept `NaN`/pandas missing values but still reject infinities.
- `y` is accepted for supervised UMAP, but that workflow is owned by the supervised/density sub-skill.
- Extra `**kwargs` pass through to the internal embedding routine; avoid them unless extending UMAP internals.

### `fit_transform(X, y=None, ensure_all_finite=True, **kwargs)`

Runs `fit` and returns the transformed result.

- With default `transform_mode='embedding'`, returns an array with shape `(n_samples, n_components)` and also sets `embedding_`.
- With `transform_mode='graph'`, returns the fitted sparse graph.
- With `output_dens=True`, returns `(embedding, rad_orig, rad_emb)`; density workflows are routed elsewhere.
- If the input dtype is floating, the returned embedding may be cast back to that dtype.

### `transform(X, ensure_all_finite=True)`

Embeds new samples into an existing fitted UMAP space.

Prerequisites and caveats:

- The estimator must already be fitted.
- If `X` is the exact training data, UMAP short-circuits and returns `embedding_` (or `graph_` in graph mode).
- If the model was fitted on one training sample, transform raises `ValueError`.
- `densmap=True` raises `NotImplementedError` for new data.
- If an accepted two-array `precomputed_knn=(indices, dists)` lacked a search index, transforming new raw samples raises `NotImplementedError` mentioning the missing search index.
- For `metric='precomputed'`, `X` must be distances from new points to training points with shape `(n_new, n_train)`, not a square new-new matrix.
- `transform` returns a new embedding and should not mutate the learned `embedding_`.

### `inverse_transform(X)`

Approximates high-dimensional samples from low-dimensional coordinates.

- Input shape is `(n_samples, n_components)` in the learned embedding space.
- Output shape is `(n_samples, n_features)` for dense original data.
- It is approximate and works best for points inside or near the convex hull of the learned embedding.
- It is unavailable for sparse original data, `metric='precomputed'`, metrics without inverse gradients, `densmap=True`, and `transform_mode='graph'`.
- It may warn or be poor for high-dimensional latent spaces (`n_components >= 8`).

### `update(X, ensure_all_finite=True)`

Mutates the fitted estimator by appending new samples and recomputing graph/embedding structures.

- The new `X` must have the same feature dimension and compatible dense/sparse type semantics as training data.
- `metric='precomputed'` raises `ValueError`: update does not support precomputed metrics.
- Supervised models raise `ValueError`: updating supervised models is not supported.
- The method mutates `self._raw_data`, `graph_`, and `embedding_`; copy or persist the estimator first if the previous embedding must be preserved.
- It returns `None` in this implementation, not `self`.

## Fitted attributes and useful diagnostics

| Attribute | Set when | Meaning and safe use |
| --- | --- | --- |
| `embedding_` | `fit`/`fit_transform` with `transform_mode='embedding'` | Training embedding, shape `(n_samples, n_components)`. Disconnected vertices can contain `NaN` coordinates. |
| `graph_` | `fit`/`fit_transform` | Fuzzy simplicial set as a sparse graph over training samples. Useful for diagnostics, composition, and graph-mode transforms. |
| `graph_dists_` | Fitting paths that request graph distances | Distances associated with graph edges; mostly internal/density support. |
| `rad_orig_`, `rad_emb_` | `output_dens=True` | Local radii in original and embedding spaces. Route interpretation to density workflows. |
| `embedding_list_` | `n_epochs` is a list and the embedding routine returns intermediate embeddings | Intermediate embedding snapshots. |
| `_n_features_out` | after fit | Number of output features for sklearn feature-name machinery: `n_components` in embedding mode or graph column count in graph mode. |
| `_raw_data` | after fit | Validated training data retained by the estimator. Private; useful only for diagnostics such as checking `n_train` for precomputed transform shapes. |
| `_knn_indices`, `_knn_dists`, `_knn_search_index` | after neighbor graph construction | Private nearest-neighbor state. `_knn_search_index is None` explains why transforming new raw samples is unavailable after two-array `precomputed_knn`. |
| `_unique_inverse_` | `unique=True` | Map from original rows to unique internal rows. Private but documented in the class docstring. |

Because many diagnostic attributes are private by naming convention, use them for troubleshooting and verification, not as long-term stable public APIs unless the task requires UMAP internals.

## Sklearn-style estimator behavior

`UMAP` subclasses sklearn `BaseEstimator`, so it supports common estimator mechanics:

- Constructor parameters are available through `get_params()` and can be set through `set_params()` before fitting.
- It can be a transformer step in `sklearn.pipeline.Pipeline` because it implements `fit`, `fit_transform`, and `transform`.
- Grid/random search can tune UMAP parameters, but stochasticity means searches should set `random_state` when exact repeatability is required.
- UMAP is an unsupervised transformer by default. Passing labels through `y` changes the algorithm; route that choice to the supervised/density sub-skill.
- UMAP does not expose console entry points.

## Precomputed distance API

Use `metric='precomputed'` when you already have distances.

Fit semantics:

```python
from sklearn.metrics import pairwise_distances
mapper = umap.UMAP(metric="precomputed", n_neighbors=10, random_state=42)
D_train = pairwise_distances(X_train)  # shape (n_train, n_train)
mapper.fit(D_train)
```

Transform semantics:

```python
D_new_to_train = pairwise_distances(X_new, X_train)  # shape (n_new, n_train)
X_new_embedding = mapper.transform(D_new_to_train)
```

Rules:

- Dense fit matrix must be square train-train distances.
- Sparse precomputed fit matrices must be symmetric and have zero diagonal.
- Transform accepts dense or sparse new-to-train distances; sparse rows must contain at least `n_neighbors` distances.
- Shape failures may appear as assertion errors because the implementation asserts `X.shape[1] == n_train` during precomputed transform. Validate shapes explicitly before calling.
- `inverse_transform` is unavailable for precomputed metrics.
- `unique=True` is invalid with precomputed metrics.
- `update` is unavailable for precomputed metrics.

## Precomputed k-NN

### Helper signature

```python
nearest_neighbors(
    X,
    n_neighbors,
    metric,
    metric_kwds,
    angular,
    random_state,
    low_memory=True,
    use_pynndescent=True,
    n_jobs=-1,
    verbose=False,
)
```

The helper returns `(knn_indices, knn_dists, knn_search_index)`:

- `knn_indices`: integer array with shape `(n_samples, k)`.
- `knn_dists`: distance array with shape `(n_samples, k)`.
- `knn_search_index`: search structure that can support later `transform` for raw new samples.

### Use a full tuple when later transform matters

```python
from umap.umap_ import nearest_neighbors

knn = nearest_neighbors(
    X_train,
    n_neighbors=50,
    metric="euclidean",
    metric_kwds=None,
    angular=False,
    random_state=42,
)
mapper = umap.UMAP(n_neighbors=30, precomputed_knn=knn, random_state=42).fit(X_train)
X_new_embedding = mapper.transform(X_new)
```

The k used to compute neighbors must be at least the UMAP `n_neighbors`. UMAP can prune excess columns.

### Use a two-array tuple only for fitting

```python
mapper = umap.UMAP(
    n_neighbors=30,
    precomputed_knn=(knn_indices, knn_dists),
    random_state=42,
).fit(X_train)
```

A two-array tuple is accepted for fitting, but it lacks a search index. Transforming new raw data raises `NotImplementedError`. This is correct behavior, not an installation failure.

### Reproducibility with precomputed k-NN

For exactly reproducible precomputed-kNN runs, keep all three aligned:

1. The random seed used when computing k-NN.
2. The k/`n_neighbors` used when computing k-NN.
3. The UMAP `random_state` used when fitting.

Changing the neighbor graph changes the high-dimensional fuzzy graph, so identical UMAP seeds alone cannot make different neighbor graphs produce identical embeddings.

## Other helpers

```python
find_ab_params(spread, min_dist)
```

Computes the internal curve parameters `a` and `b` for a chosen `spread` and `min_dist`. Most users should leave constructor `a=None, b=None` so UMAP calls this automatically.

`fuzzy_simplicial_set` and lower-level layout functions exist in `umap.umap_`, but they are internal construction primitives. Prefer the estimator API unless implementing advanced graph workflows.
