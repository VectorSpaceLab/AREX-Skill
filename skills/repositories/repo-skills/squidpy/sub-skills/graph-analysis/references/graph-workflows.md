# Graph Workflows

This reference distills Squidpy graph construction and statistics into safe reusable workflows. It assumes data is already loaded into an `AnnData` object or a `SpatialData` table; route loading and spatial metadata validation to `datasets-and-io`.

## Minimal AnnData Preconditions

```python
import pandas as pd
import squidpy as sq

assert "spatial" in adata.obsm
assert adata.obsm["spatial"].shape[0] == adata.n_obs

cluster_key = "cell_type"
adata.obs[cluster_key] = adata.obs[cluster_key].astype("category")
```

For `SpatialData`, most graph analysis functions accept `AnnData | SpatialData` but require `table_key`. Graph construction from `SpatialData` also needs `elements_to_coordinate_systems` when coordinates should be derived from shapes or labels and attached to the selected table under `spatial_key`.

## Build Spatial Neighbor Graphs

Prefer the mode-specific graph constructors. The older `sq.gr.spatial_neighbors` compatibility entry point is deprecated in the inspected API version; use it only when maintaining old snippets.

```python
import squidpy as sq

# Generic continuous coordinates; fixed neighborhood size.
sq.gr.spatial_neighbors_knn(adata, n_neighs=6, key_added="spatial")

# Physical-distance scale; a tuple keeps only an annulus.
sq.gr.spatial_neighbors_radius(adata, radius=50.0, key_added="spatial")
sq.gr.spatial_neighbors_radius(adata, radius=(20.0, 80.0), key_added="spatial")

# Adaptive geometric graph; optional radius prunes edges after triangulation.
sq.gr.spatial_neighbors_delaunay(adata, radius=None, key_added="spatial")

# Visium-like regular lattice; distances encode ring/grid distance.
sq.gr.spatial_neighbors_grid(adata, n_neighs=6, n_rings=1, key_added="spatial")
```

Default storage for `key_added="spatial"`:

- `adata.obsp['spatial_connectivities']`: sparse adjacency/connectivity matrix.
- `adata.obsp['spatial_distances']`: sparse distance matrix with the same edge structure.
- `adata.uns['spatial']`: metadata with `connectivities_key`, `distances_key`, and builder `params`.

With `key_added="mygraph"`, outputs become `mygraph_connectivities`, `mygraph_distances`, and `adata.uns['mygraph']`. When a downstream function accepts `connectivity_key`, pass either `"mygraph"` to functions that call Squidpy's key helper, or the full key where the signature explicitly defaults to `"spatial_connectivities"`. The safest pattern is to inspect `adata.uns['mygraph']['connectivities_key']` and pass that concrete key when accepted.

## Choosing a Builder

| Goal | Use | Important Tradeoffs |
|---|---|---|
| Constant local neighborhood size | `spatial_neighbors_knn(n_neighs=...)` | Good for generic point clouds; large `n_neighs` makes broader, denser graphs. |
| Physical interaction radius | `spatial_neighbors_radius(radius=...)` | Sensitive to coordinate units; tuple radius keeps edges in `[min, max]`. |
| Geometry-driven adaptive graph | `spatial_neighbors_delaunay(radius=...)` | Triangulation is independent of radius; scalar radius prunes to `(0, r)`. |
| Visium-like lattice/rings | `spatial_neighbors_grid(n_neighs=6, n_rings=...)` | Intended for regular grids; distance matrix stores ring distance rather than Euclidean distance. |
| Custom backend | `spatial_neighbors_from_builder(adata, builder)` | Implement `GraphBuilder` or `GraphBuilderCSR`; see `custom-builders.md`. |

Common graph parameters:

- `spatial_key`: coordinate matrix in `.obsm`; default is `"spatial"`.
- `library_key`: categorical `.obs` column used to build separate per-library blocks.
- `elements_to_coordinate_systems`: `SpatialData` mapping from element names to coordinate systems for coordinate extraction.
- `table_key`: `SpatialData` table to read and update.
- `transform`: adjacency transform, commonly `None`, `"spectral"`, or `"cosine"`.
- `percentile`: prunes generic graph distances by distance percentile.
- `set_diag`: sets self-connectivities to `1.0`; distances keep a zero diagonal.
- `n_jobs`: parallelizes per-library graph construction, not every statistic.

## SpatialData Construction Pattern

```python
sq.gr.spatial_neighbors_knn(
    sdata,
    table_key="table",
    elements_to_coordinate_systems={"cells": "global"},
    n_neighs=8,
    key_added="spatial",
)

adata = sdata.tables["table"]
assert "spatial_connectivities" in adata.obsp
```

Use `table_key` again for downstream graph statistics when passing the `SpatialData` object directly:

```python
sq.gr.nhood_enrichment(
    sdata,
    table_key="table",
    cluster_key="cell_type",
    n_perms=100,
    seed=0,
    n_jobs=1,
    show_progress_bar=False,
)
```

If the selected table already has `adata.obsm['spatial']`, you may call graph functions on the `AnnData` table itself and avoid `SpatialData` coordinate extraction. Use `SpatialData` only when the task needs element-to-coordinate-system semantics or graph masking.

## Common Statistical Pipeline

```python
cluster_key = "cell_type"
adata.obs[cluster_key] = adata.obs[cluster_key].astype("category")

sq.gr.spatial_neighbors_knn(adata, n_neighs=6)

sq.gr.nhood_enrichment(
    adata,
    cluster_key=cluster_key,
    n_perms=100,
    seed=0,
    n_jobs=1,
    show_progress_bar=False,
)
sq.gr.centrality_scores(adata, cluster_key=cluster_key, n_jobs=1)
sq.gr.interaction_matrix(adata, cluster_key=cluster_key, normalized=True)
sq.gr.co_occurrence(adata, cluster_key=cluster_key, interval=20)
sq.gr.spatial_autocorr(adata, genes=["GeneA", "GeneB"], mode="moran", n_perms=None)
sq.gr.ripley(adata, cluster_key=cluster_key, mode="L", n_simulations=10, n_observations=100, n_steps=20)
```

Result storage:

- `nhood_enrichment`: `adata.uns[f'{cluster_key}_nhood_enrichment']['zscore']` and `['count']`.
- `centrality_scores`: `adata.uns[f'{cluster_key}_centrality_scores']` as a DataFrame.
- `interaction_matrix`: `adata.uns[f'{cluster_key}_interactions']` as a cluster-by-cluster array.
- `co_occurrence`: `adata.uns[f'{cluster_key}_co_occurrence']['occ']` and `['interval']`.
- `spatial_autocorr`: `adata.uns['moranI']` or `adata.uns['gearyC']`.
- `ripley`: `adata.uns[f'{cluster_key}_{mode}_ripley']` with statistic, simulations, bins, and p-values.
- `ligrec`: default `adata.uns[f'{cluster_key}_ligrec']` or a key controlled by `key_added`.
- `sepal`: `adata.uns['sepal_score']`.
- `calculate_niche`: niche labels are added to `adata.obs` columns such as `nhood_niche_res=0.5`, `utag_niche_res=0.5`, `cellcharter_niche`, or `spatialleiden_res=...`.

## Ligand-Receptor Workflow

Provide `interactions` explicitly for offline/reproducible use. If omitted, Squidpy fetches interactions from OmniPath, which may require network access and optional dependency availability.

```python
import pandas as pd

interactions = pd.DataFrame(
    {"source": ["LIG1", "LIG2"], "target": ["REC1", "REC2"]}
)

adata.obs["cell_type"] = adata.obs["cell_type"].astype("category")
adata.raw = adata.copy()  # only if use_raw=True is desired and raw contains these genes

sq.gr.ligrec(
    adata,
    cluster_key="cell_type",
    interactions=interactions,
    use_raw=True,
    n_perms=100,
    seed=0,
    n_jobs=1,
    show_progress_bar=False,
)
```

`ligrec` returns or stores a mapping with `means`, `pvalues`, and `metadata`. The `means` and `pvalues` frames use interaction pairs as a MultiIndex and cluster-pair columns. Use `gene_symbols="column_name"` when interaction names match `adata.var[column_name]` rather than `adata.var_names`.

## Niche Workflows

`calculate_niche` uses a spatial connectivity graph and writes labels into `adata.obs`. Build `spatial_connectivities` first.

```python
sq.gr.spatial_neighbors_knn(adata, n_neighs=8)

sq.gr.calculate_niche(
    adata,
    flavor="neighborhood",
    groups="cell_type",
    n_neighbors=10,
    resolutions=[0.3, 0.8],
    min_niche_size=5,
    spatial_connectivities_key="spatial_connectivities",
)
```

Flavor-specific notes:

- `neighborhood`: needs `groups`, `n_neighbors`, and `resolutions`; clusters neighborhood profiles.
- `utag`: needs `n_neighbors` and `resolutions`; uses adjacency-smoothed feature matrix.
- `cellcharter`: can use `distance`, `aggregation`, `n_components`, and optionally `use_rep`; may densify aggregated matrices, so size matters.
- `spatialleiden`: needs both `spatial_connectivities_key` and a latent `connectivities` graph from `scanpy.pp.neighbors`; install optional Leiden support with `squidpy[leiden]` when the environment lacks `spatialleiden`.

## Sepal Workflow

`sepal` identifies spatially variable genes using a diffusion process on grid-like graphs. It validates that every node has the requested maximum degree.

```python
sq.gr.spatial_neighbors_grid(adata, n_neighs=6, n_rings=1)
scores = sq.gr.sepal(
    adata,
    max_neighs=6,
    genes=["GeneA", "GeneB"],
    n_iter=1000,
    copy=True,
    n_jobs=1,
    show_progress_bar=False,
)
```

Use `max_neighs=4` for square-grid data and `max_neighs=6` for hexagonal Visium-like data. If the graph has a different maximum degree, rebuild the graph or choose a statistic less tied to grid topology.

## Physical-Radius Xenium-Style Workflow

For molecule or cell centroid point clouds where coordinates are in physical units, use a radius graph and make the result key explicit before spatial autocorrelation.

```python
sq.gr.spatial_neighbors_radius(
    adata,
    radius=35.0,
    spatial_key="spatial",
    key_added="xenium_radius35",
    n_jobs=1,
)
conn_key = adata.uns["xenium_radius35"]["connectivities_key"]

moran = sq.gr.spatial_autocorr(
    adata,
    connectivity_key=conn_key,
    genes=["GeneA"],
    mode="moran",
    n_perms=None,
    copy=True,
    n_jobs=1,
    show_progress_bar=False,
)
```

This pattern avoids accidentally reading the default `spatial_connectivities` from an older graph.

## Graph Masking

`mask_graph` is for `SpatialData` and a Shapely `Polygon` or `MultiPolygon`. It masks edges from an existing graph based on whether edge line segments are fully contained in the polygon.

```python
from shapely import Polygon

sq.gr.mask_graph(
    sdata,
    table_key="table",
    polygon_mask=Polygon([...]),
    spatial_key="spatial",
    key_added="mask",
)
```

If `spatial_key="spatial"` and `key_added="mask"`, masked outputs are stored as `mask_spatial_connectivities`, `mask_spatial_distances`, and `mask_spatial`. `negative_mask=True` removes fully contained edges instead of keeping only contained edges.

## Safe Validation Snippets

```python
conn = adata.obsp["spatial_connectivities"]
dist = adata.obsp["spatial_distances"]
assert conn.shape == dist.shape == (adata.n_obs, adata.n_obs)
assert conn.nnz > 0

assert str(adata.obs["cell_type"].dtype) == "category"
assert not adata.obs["cell_type"].isna().all()

assert adata.uns["spatial"]["connectivities_key"] == "spatial_connectivities"
```
