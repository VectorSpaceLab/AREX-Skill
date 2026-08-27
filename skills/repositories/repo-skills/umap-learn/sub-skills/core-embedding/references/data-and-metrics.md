# Data Formats, Metrics, and Parameter Decisions

This reference covers data and metric choices for base `umap.UMAP` workflows.

## Input data formats

### Dense numeric arrays

Use ordinary numeric arrays with shape `(n_samples, n_features)`:

```python
import numpy as np
import umap

X = np.asarray(X, dtype=np.float32)
mapper = umap.UMAP(metric="euclidean", random_state=42).fit(X)
```

UMAP validates ordinary data with sklearn's array checks and casts to `float32` for most metrics. Rows are samples; columns are features.

### Pandas and sklearn data

UMAP can consume array-like objects that sklearn can validate, including many pandas DataFrames and outputs from sklearn preprocessors. Operational guidance:

- UMAP uses row order; preserve row alignment with labels, metadata, train/test splits, and downstream targets.
- DataFrame indexes and column names are not the core UMAP representation after validation. Keep your own mapping from embedding rows back to records.
- Scale continuous features before UMAP when Euclidean-like metrics should treat features comparably.
- In sklearn pipelines, remember that passing `y` to `UMAP.fit(X, y)` changes the workflow to supervised UMAP; route intentional supervised use to `../../supervised-density/SKILL.md`.

### Sparse matrices

UMAP supports scipy sparse matrices directly, with CSR as the safest format.

```python
from scipy import sparse
mapper = umap.UMAP(metric="cosine", random_state=42, low_memory=True).fit(sparse.csr_matrix(X))
```

Sparse guidance:

- Use sparse-friendly metrics from the catalog below.
- `transform` also accepts sparse held-out rows with the same feature dimension.
- `inverse_transform` is not available after fitting on sparse input.
- `metric='precomputed'` sparse matrices have additional distance-matrix rules below.

### Precomputed distance matrices

With `metric="precomputed"`, the meaning of `X` changes from features to distances.

| Call | Required shape | Meaning |
| --- | --- | --- |
| `fit(D_train)` / `fit_transform(D_train)` | `(n_train, n_train)` | Square pairwise distances among training samples. |
| `transform(D_new_to_train)` | `(n_new, n_train)` | Distances from each new sample to each original training sample. |

Rules:

- The fit matrix should have zero self-distances. Sparse precomputed fit matrices must be symmetric and have zero diagonal.
- Sparse precomputed rows must contain enough distances for neighbor selection; transform rows need at least `n_neighbors` stored distances.
- Transform does not accept a square new-new distance matrix unless its second dimension happens to equal the original training count and its columns are in the original training-row order.
- `inverse_transform`, `update`, and `unique=True` are unavailable for precomputed metrics.

### Precomputed k-NN tuples

Use `precomputed_knn` when you have neighbor indices and distances instead of a full distance matrix.

Expected tuple contents:

- Full tuple: `(knn_indices, knn_dists, knn_search_index)`.
- Fit-only tuple: `(knn_indices, knn_dists)`.

Shape requirements:

- `knn_indices.shape == knn_dists.shape == (n_samples, k)`.
- `k >= UMAP(..., n_neighbors=...)`.
- Rows correspond exactly to the fit data rows.
- The nearest neighbor of each item should be itself in normal UMAP neighbor graphs.

A full tuple from `umap.umap_.nearest_neighbors` can support later raw-data `transform`; a fit-only tuple cannot.

## Metric catalog

UMAP metric strings are implemented in `umap.distances`, `umap.sparse`, and PyNNDescent. The most common user-facing categories are below.

### Dense input metrics

| Category | Metric names | Notes |
| --- | --- | --- |
| Euclidean/Minkowski style | `euclidean`, `l2`, `manhattan`, `taxicab`, `l1`, `chebyshev`, `linfinity`, `linfty`, `linf`, `minkowski` | Good for scaled continuous features. `minkowski` can use `metric_kwds` such as `p`. |
| Weighted/standardized spatial | `seuclidean`, `standardised_euclidean`, `wminkowski`, `weighted_minkowski`, `mahalanobis` | Require appropriate scale/covariance/weight keyword arguments. |
| Miscellaneous spatial | `canberra`, `braycurtis`, `haversine`, `poincare` | `haversine` is defined for two-dimensional latitude/longitude-like inputs. |
| Angular/correlation | `cosine`, `correlation` | Useful for vector direction, text embeddings, normalized high-dimensional features. UMAP automatically treats these as angular-neighbor-search metrics. |
| Probability/divergence style | `hellinger`, `softmax_hellinger`, `ll_dirichlet`, `symmetric_kl` | Check data domain. `hellinger` rejects negative input. |
| Binary/set style | `hamming`, `jaccard`, `dice`, `matching`, `kulsinski`, `rogerstanimoto`, `russellrao`, `sokalsneath`, `sokalmichener`, `yule` | Best for binary/boolean or set-like features; disconnected vertices are common when rows share no features. |
| Discrete/string-like | `categorical`, `ordinal`, `hierarchical_categorical`, `count`, `string`, `myers` | Mostly useful in supervised/target or specialized distance contexts; route label-driven use to the supervised/density sub-skill. |
| Precomputed | `precomputed` | Input is distances, not features. |

### Sparse input metrics

Sparse-specific metric implementations include:

- Continuous/spatial: `euclidean`, `manhattan`, `l1`, `taxicab`, `chebyshev`, `linf`, `linfty`, `linfinity`, `minkowski`, `canberra`, `braycurtis`, `cosine`, `correlation`, `hellinger`, `ll_dirichlet`.
- Binary/set: `hamming`, `jaccard`, `dice`, `matching`, `kulsinski`, `rogerstanimoto`, `russellrao`, `sokalmichener`, `sokalsneath`.

If a metric is valid for dense data but not for sparse data, UMAP raises `ValueError` saying the metric is not supported for sparse data.

### Output metrics

`output_metric` controls distances in the low-dimensional embedding. The default and most tested choice is `euclidean`.

Output metrics must have gradients. Built-in gradient-backed output metrics include:

`euclidean`, `l2`, `manhattan`, `taxicab`, `l1`, `chebyshev`, `linfinity`, `linfty`, `linf`, `minkowski`, `seuclidean`, `standardised_euclidean`, `wminkowski`, `weighted_minkowski`, `mahalanobis`, `canberra`, `cosine`, `correlation`, `hellinger`, `softmax_hellinger`, `haversine`, `braycurtis`, `symmetric_kl`, `spherical_gaussian_energy`, `diagonal_gaussian_energy`, `gaussian_energy`, `hyperboloid`.

Invalid output choices:

- `output_metric="precomputed"` raises `ValueError`.
- A metric with no gradient implementation raises `ValueError` for output use.
- densMAP supports only Euclidean/l2 output; route densMAP tasks to `../../supervised-density/SKILL.md`.

## Custom metric caveats

UMAP accepts callable `metric` values, but performance and method support depend on numba compatibility.

### Dense custom metric returning distance only

```python
import numba
import numpy as np
import umap

@numba.njit()
def l1_custom(x, y):
    return np.sum(np.abs(x - y))

mapper = umap.UMAP(metric=l1_custom, random_state=42).fit(X)
```

A distance-only custom input metric can fit, but UMAP warns that `inverse_transform` is unavailable because no gradient is returned.

### Dense custom metric with gradient

```python
@numba.njit()
def l1_with_grad(x, y):
    diff = x - y
    return np.sum(np.abs(diff)), np.sign(diff)

mapper = umap.UMAP(metric=l1_with_grad, random_state=42).fit(X)
```

Returning `(distance, gradient)` enables inverse-transform support when the rest of the configuration permits it.

### Custom output metric

A callable `output_metric` must return `(distance, gradient)`. A distance-only output metric raises `ValueError` during fit.

### Sparse custom metrics

Sparse custom callables are advanced. UMAP checks sparse callable metrics using index/data arrays rather than dense 1D arrays. Prefer built-in sparse metrics unless you are prepared to match UMAP's sparse metric calling conventions and test both fit and transform.

### `metric_kwds` and ordering

UMAP forwards `metric_kwds` values into numba-compiled metric calls. The source notes that ordered keyword handling can matter for metrics with multiple parameters. Use explicit, stable dictionaries and test the metric with a tiny smoke case before long runs.

## Parameter decision guide

| Parameter | First choice | Change when | Failure or trade-off to watch |
| --- | --- | --- | --- |
| `n_neighbors` | `15` | Lower for fine local detail; higher for global structure or smoother density estimates. | Too small can fragment the graph; too large may hide local structure. Must be > 1. |
| `min_dist` | `0.1` | Lower for compact/clumpy clusters; higher for more even spacing. | Must be `0 <= min_dist <= spread`. Clumpy visual clusters are not proof of true classes. |
| `n_components` | `2` for visualization | Use higher values for downstream ML features. | `inverse_transform` warns and may degrade when `n_components >= 8`. |
| `metric` | Match data semantics | Use `cosine` for directional vectors, sparse-friendly metrics for sparse data, `precomputed` for distance matrices. | Bad names raise `ValueError`; domain violations such as negative Hellinger data fail. |
| `output_metric` | `euclidean` | Use specialist embedding geometries only when required. | Must have gradient; not all input metrics are valid output metrics. |
| `random_state` | Set an int for reports and exact repeatability | Leave `None` for faster multicore stochastic runs. | Setting it makes UMAP override effective `n_jobs` to `1`. |
| `n_jobs` | `-1` for speed-oriented unseeded runs | Set positive integer to limit threads. | `0` or `< -1` fails. Ignored/overridden when `random_state` is set. |
| `low_memory` | `True` in 0.5.12 | Set `False` only when memory is ample and speed matters. | Lower-memory path can be slower. |
| `force_approximation_algorithm` | `False` | Set `True` to use approximate NN behavior on smaller data or align with large-data path. | Ignored when accepted `precomputed_knn` is used. |
| `transform_seed` | `42` | Change to intentionally vary stochastic transform initialization. | Does not make the original fit reproducible; use `random_state` for that. |
| `unique` | `False` | Set `True` for many duplicate rows. | Invalid with precomputed metrics; changes internal row handling. |
| `disconnection_distance` | `None` | Set manually for bounded metrics when maximally distant points artificially connect the graph. | Disconnected vertices become `NaN` in `embedding_`; filter or investigate them. |

## Reproducibility and performance

- `random_state` makes layouts reproducible for a fixed environment, input, and neighbor graph.
- UMAP uses parallel optimization when `random_state=None`; exact reproducibility and maximum parallelism are intentionally at odds.
- When `random_state` is not `None` and `n_jobs != 1`, UMAP sets `n_jobs` to `1` and warns.
- First runs may be slower due to numba JIT compilation.
- `NUMBA_NUM_THREADS` can cap numba thread use if set before Python starts.
- Optional `tbb` may improve CPU performance on supported x86 systems, but it is not required for correctness and was not installed in the minimum verified environment.
- This package's core `umap.UMAP` is CPU-oriented. If a task explicitly asks for a GPU UMAP implementation, do not claim core `umap.UMAP` provides GPU acceleration; use a separate GPU implementation chosen by the user.

## DensMAP route note

The base constructor includes `densmap`, `dens_lambda`, `dens_frac`, `dens_var_shift`, and `output_dens`. Those parameters change the optimization objective and returned values. For any task focused on density preservation, local radii, `output_dens`, clustering/outlier interpretation, or supervised labels, route to `../../supervised-density/SKILL.md`.
