# Custom Graph Builders

Squidpy exposes `squidpy.gr.neighbors` for custom graph construction. Use this when built-in KNN, radius, Delaunay, and grid builders do not match a task, such as approximate nearest-neighbor search or a domain-specific adjacency rule.

## Builder Classes

- `GraphBuilder(transform=None, set_diag=False, percentile=None, postprocessors=())`: generic pipeline for custom coordinate types or matrix backends.
- `GraphBuilderCSR(transform=None, set_diag=False, percentile=None, postprocessors=())`: CSR-specialized base class for builders returning `scipy.sparse.csr_matrix`; it reuses sparse warning suppression and multi-library block combination.
- Built-ins: `KNNBuilder(n_neighs=6, ...)`, `RadiusBuilder(radius, ...)`, `DelaunayBuilder(radius=None, ...)`, and `GridBuilder(n_neighs=6, n_rings=1, delaunay=False, ...)`.
- Reusable postprocessors: `DistanceIntervalPostprocessor(interval)`, `PercentilePostprocessor(percentile)`, and `TransformPostprocessor(transform)`.

A builder receives a coordinate array and returns `(adj, dst)`:

- `adj`: square adjacency/connectivity matrix of shape `(n_obs, n_obs)` where non-zero entries are edges.
- `dst`: square distance/value matrix with the same edge structure.
- For `GraphBuilderCSR`, both matrices should be `csr_matrix`.
- `dst` should usually have a zero diagonal; `adj` should only have a non-zero diagonal when `set_diag=True`.

## Required Methods

| Base | Member | Required | Purpose |
|---|---|---|---|
| `GraphBuilder` | `build_graph(coords)` | Yes | Construct and return raw `(adj, dst)`. |
| `GraphBuilder` | `uns_params()` | Yes | Return metadata saved under `adata.uns[key_added]['params']`. |
| `GraphBuilder` | `postprocessors()` | No | Return operations applied after `build_graph`; can also pass `postprocessors=` to `super().__init__()`. |
| `GraphBuilder` | `combine(mats, ixs)` | Only for custom multi-library support | Combine per-library graph blocks. `GraphBuilderCSR` already implements block-diagonal combination. |

## Approximate KNN Pattern

The pattern below is intentionally backend-agnostic. Replace `query_approximate_neighbors` with a library such as `pynndescent`, FAISS, Annoy, or a project-local index. Keep optional dependencies outside the public skill runtime unless the user chooses to install them.

```python
import numpy as np
from scipy.sparse import csr_matrix
from squidpy.gr.neighbors import GraphBuilderCSR

class ApproxKNNBuilder(GraphBuilderCSR):
    def __init__(self, n_neighs=6, **kwargs):
        super().__init__(**kwargs)
        self.n_neighs = n_neighs

    def uns_params(self):
        return {
            "coord_type": "generic",
            "n_neighbors": self.n_neighs,
            "backend": "custom-approx-knn",
            "transform": self.transform.v,
        }

    def build_graph(self, coords):
        n_obs = coords.shape[0]
        indices, distances = query_approximate_neighbors(coords, k=self.n_neighs)
        rows = np.repeat(np.arange(n_obs), self.n_neighs)
        cols = indices.reshape(-1)
        vals = distances.reshape(-1).astype(float)

        adj = csr_matrix(
            (np.ones(rows.shape[0], dtype=np.float32), (rows, cols)),
            shape=(n_obs, n_obs),
        )
        dst = csr_matrix((vals, (rows, cols)), shape=(n_obs, n_obs))
        adj.setdiag(1.0 if self.set_diag else adj.diagonal())
        dst.setdiag(0.0)
        return adj, dst
```

Use the builder through Squidpy so storage keys and downstream functions stay standard:

```python
builder = ApproxKNNBuilder(n_neighs=12, transform=None, set_diag=False)
sq.gr.spatial_neighbors_from_builder(adata, builder=builder, key_added="approx")
```

Outputs are `adata.obsp['approx_connectivities']`, `adata.obsp['approx_distances']`, and `adata.uns['approx']`. Downstream statistics must use the matching connectivity key, for example `sq.gr.nhood_enrichment(adata, "cell_type", connectivity_key="approx")` or `connectivity_key="approx_connectivities"` depending on the function.

## Multi-Library Behavior

If the user passes `library_key`, Squidpy builds one graph per library. `GraphBuilderCSR.combine` creates a block-diagonal graph and reorders back to the original observation order when needed. If a custom builder inherits plain `GraphBuilder`, implement `combine` before supporting `library_key`; otherwise advise users to subset by library manually or omit `library_key`.

For multi-library analysis, verify each library has enough observations for the chosen graph mode. A KNN graph with `n_neighs=12` cannot be meaningful for a library with fewer than 13 observations unless the backend handles self-neighbors and pruning carefully.

## Postprocessor Composition

Use public postprocessors rather than manually rewriting common pruning/transformation logic.

```python
from squidpy.gr.neighbors import (
    DistanceIntervalPostprocessor,
    TransformPostprocessor,
)

class AnnulusBuilder(GraphBuilderCSR):
    def __init__(self, radius=(10.0, 50.0), transform=None, **kwargs):
        super().__init__(
            transform=transform,
            postprocessors=[
                DistanceIntervalPostprocessor(tuple(sorted(radius))),
                TransformPostprocessor(transform),
            ],
            **kwargs,
        )
```

Keep the `adj` and `dst` sparsity structures aligned before and after postprocessors. A malformed custom builder can silently corrupt downstream statistics if adjacency and distance matrices disagree.

## Validation Checklist

```python
sq.gr.spatial_neighbors_from_builder(adata, builder=builder, key_added="custom")
conn = adata.obsp["custom_connectivities"]
dist = adata.obsp["custom_distances"]
assert conn.shape == dist.shape == (adata.n_obs, adata.n_obs)
assert conn.nnz > 0
assert set(adata.uns["custom"]) >= {"connectivities_key", "distances_key", "params"}
```

For approximate backends, compare a small sample against `spatial_neighbors_knn` to verify scale, degree distribution, and self-edge behavior before using statistics such as enrichment or autocorrelation.

```python
sq.gr.spatial_neighbors_knn(adata, n_neighs=12, key_added="exact")
assert adata.obsp["custom_connectivities"].shape == adata.obsp["exact_connectivities"].shape
```
