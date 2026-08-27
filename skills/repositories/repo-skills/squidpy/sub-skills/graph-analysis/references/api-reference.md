# Graph API Reference

This reference lists the public `squidpy.gr` APIs covered by this sub-skill. Signatures reflect live package inspection from the generated skill build.

## Graph Builders And Postprocessors

### `sq.gr.spatial_neighbors`

```python
sq.gr.spatial_neighbors(
    adata,
    spatial_key="spatial",
    elements_to_coordinate_systems=None,
    table_key=None,
    library_key=None,
    coord_type=None,
    n_neighs=None,
    radius=None,
    delaunay=None,
    n_rings=None,
    percentile=None,
    transform=None,
    set_diag=False,
    key_added="spatial",
    copy=False,
    n_jobs=1,
)
```

Compatibility entry point that chooses grid, KNN, radius, or Delaunay mode from `coord_type`, `radius`, and `delaunay`. It is deprecated in the inspected API version; prefer the mode-specific functions below. It stores `obsp[f'{key_added}_connectivities']`, `obsp[f'{key_added}_distances']`, and `uns[key_added]` unless `copy=True` returns a `SpatialNeighborsResult`.

### `sq.gr.spatial_neighbors_knn`

```python
sq.gr.spatial_neighbors_knn(
    data,
    *,
    spatial_key="spatial",
    elements_to_coordinate_systems=None,
    table_key=None,
    library_key=None,
    n_neighs=6,
    percentile=None,
    transform=None,
    set_diag=False,
    key_added="spatial",
    copy=False,
    n_jobs=1,
)
```

Builds a generic Euclidean KNN graph. Use this for continuous coordinates when a fixed neighborhood size is desired.

### `sq.gr.spatial_neighbors_radius`

```python
sq.gr.spatial_neighbors_radius(
    data,
    *,
    radius,
    spatial_key="spatial",
    elements_to_coordinate_systems=None,
    table_key=None,
    library_key=None,
    percentile=None,
    transform=None,
    set_diag=False,
    key_added="spatial",
    copy=False,
    n_jobs=1,
)
```

Builds a radius graph. A scalar `radius` keeps points within that distance; a tuple builds with the maximum and prunes to `[min(radius), max(radius)]`.

### `sq.gr.spatial_neighbors_delaunay`

```python
sq.gr.spatial_neighbors_delaunay(
    data,
    *,
    spatial_key="spatial",
    elements_to_coordinate_systems=None,
    table_key=None,
    library_key=None,
    radius=None,
    percentile=None,
    transform=None,
    set_diag=False,
    key_added="spatial",
    copy=False,
    n_jobs=1,
)
```

Builds a Delaunay triangulation. `radius` prunes the finished graph; it does not change the triangulation. A scalar is equivalent to `(0.0, radius)`.

### `sq.gr.spatial_neighbors_grid`

```python
sq.gr.spatial_neighbors_grid(
    data,
    *,
    spatial_key="spatial",
    elements_to_coordinate_systems=None,
    table_key=None,
    library_key=None,
    n_neighs=6,
    n_rings=1,
    delaunay=False,
    transform=None,
    set_diag=False,
    key_added="spatial",
    copy=False,
    n_jobs=1,
)
```

Builds a grid/ring graph for Visium-like coordinates. With `n_rings > 1`, the distance matrix encodes ring distance. `n_neighs=6` is typical for hexagonal Visium-like grids; `n_neighs=4` is typical for square grids.

### `sq.gr.spatial_neighbors_from_builder`

```python
sq.gr.spatial_neighbors_from_builder(
    data,
    builder,
    *,
    spatial_key="spatial",
    elements_to_coordinate_systems=None,
    table_key=None,
    library_key=None,
    key_added="spatial",
    copy=False,
    n_jobs=1,
)
```

Runs an explicit `squidpy.gr.neighbors.GraphBuilder` or `GraphBuilderCSR` instance. Built-in builders include `KNNBuilder`, `RadiusBuilder`, `DelaunayBuilder`, and `GridBuilder`. Public postprocessors include `DistanceIntervalPostprocessor`, `PercentilePostprocessor`, and `TransformPostprocessor`.

### `sq.gr.mask_graph`

```python
sq.gr.mask_graph(
    sdata,
    table_key,
    polygon_mask,
    negative_mask=False,
    spatial_key="spatial",
    key_added="mask",
    copy=False,
)
```

Masks an existing `SpatialData` table graph using a Shapely `Polygon` or `MultiPolygon`. Reads the unmasked graph from `spatial_key`-derived graph keys and stores masked keys as `f'{key_added}_{spatial_key}_connectivities'`, `f'{key_added}_{spatial_key}_distances'`, and `f'{key_added}_{spatial_key}'`.

## Cluster And Graph Statistics

### `sq.gr.nhood_enrichment`

```python
sq.gr.nhood_enrichment(
    adata,
    cluster_key,
    library_key=None,
    connectivity_key=None,
    n_perms=1000,
    numba_parallel=False,
    seed=None,
    copy=False,
    n_jobs=None,
    backend="loky",
    show_progress_bar=True,
    *,
    table_key=None,
)
```

Preconditions: categorical `adata.obs[cluster_key]`; graph in `adata.obsp[connectivity_key or 'spatial_connectivities']`; categorical `library_key` if supplied. Stores `adata.uns[f'{cluster_key}_nhood_enrichment']` with `zscore` and `count`, or returns `NhoodEnrichmentResult` when `copy=True`.

### `sq.gr.centrality_scores`

```python
sq.gr.centrality_scores(
    adata,
    cluster_key,
    score=None,
    connectivity_key=None,
    copy=False,
    n_jobs=None,
    backend="loky",
    show_progress_bar=False,
    *,
    table_key=None,
)
```

Preconditions: categorical cluster labels and a connectivity graph. `score=None` computes closeness, clustering, and degree. Stores `adata.uns[f'{cluster_key}_centrality_scores']` or returns a DataFrame.

### `sq.gr.interaction_matrix`

```python
sq.gr.interaction_matrix(
    adata,
    cluster_key,
    connectivity_key=None,
    normalized=False,
    copy=False,
    weights=False,
    *,
    table_key=None,
)
```

Counts edges between clusters. `weights=False` binarizes edge presence; `weights=True` sums graph weights. Stores `adata.uns[f'{cluster_key}_interactions']` or returns an array.

### `sq.gr.co_occurrence`

```python
sq.gr.co_occurrence(
    adata,
    cluster_key,
    spatial_key="spatial",
    interval=50,
    copy=False,
    *,
    table_key=None,
)
```

Preconditions: categorical cluster labels and spatial coordinates. `interval` can be an integer number of uniformly spaced distance thresholds or a sequence of thresholds with length at least 2. Stores `adata.uns[f'{cluster_key}_co_occurrence']` with `occ` and `interval`, or returns `(occ, interval)`.

### `sq.gr.spatial_autocorr`

```python
sq.gr.spatial_autocorr(
    adata,
    connectivity_key="spatial_connectivities",
    genes=None,
    mode="moran",
    transformation=True,
    n_perms=None,
    two_tailed=False,
    corr_method="fdr_bh",
    attr="X",
    layer=None,
    seed=None,
    use_raw=False,
    copy=False,
    n_jobs=None,
    backend="loky",
    show_progress_bar=True,
    *,
    table_key=None,
)
```

Computes Moran's I (`mode="moran"`) or Geary's C (`mode="geary"`). `attr="X"` uses genes in `.var_names`; `attr="obs"` uses numeric `.obs` columns; `attr="obsm"` uses indices in `.obsm[layer]`. Stores `adata.uns['moranI']` or `adata.uns['gearyC']`, or returns a DataFrame.

### `sq.gr.ripley`

```python
sq.gr.ripley(
    adata,
    cluster_key,
    mode="F",
    spatial_key="spatial",
    metric="euclidean",
    n_neigh=2,
    n_simulations=100,
    n_observations=1000,
    max_dist=None,
    n_steps=50,
    seed=None,
    copy=False,
    *,
    table_key=None,
)
```

Preconditions: categorical labels and spatial coordinates. Modes `"F"`, `"G"`, and `"L"` compute different point-process statistics. Stores `adata.uns[f'{cluster_key}_{mode}_ripley']` or returns a mapping with statistic frames, simulations, bins, and p-values.

## Expression And Interaction Statistics

### `sq.gr.ligrec`

```python
sq.gr.ligrec(
    adata,
    cluster_key,
    interactions=None,
    complex_policy="min",
    threshold=0.01,
    corr_method=None,
    corr_axis="clusters",
    use_raw=True,
    copy=False,
    key_added=None,
    gene_symbols=None,
    *,
    table_key=None,
    **kwargs,
)
```

Performs a CellPhoneDB-style permutation test. Preconditions: categorical `cluster_key`, at least two categories, expression data containing interaction genes, and `.raw` present when `use_raw=True`. `interactions` should be a DataFrame or mapping with `source` and `target` columns, or a sequence of 2-tuples. Omitting `interactions` triggers OmniPath fetching. Stores `adata.uns[f'{cluster_key}_ligrec']` by default or returns a mapping with `means`, `pvalues`, and `metadata`.

### `sq.gr.sepal`

```python
sq.gr.sepal(
    adata,
    max_neighs,
    genes=None,
    n_iter=30000,
    dt=0.001,
    thresh=1e-8,
    connectivity_key="spatial_connectivities",
    spatial_key="spatial",
    layer=None,
    use_raw=False,
    copy=False,
    n_jobs=None,
    show_progress_bar=True,
    *,
    table_key=None,
)
```

Computes Sepal spatial variability scores. `max_neighs` must be `4` or `6`, and the graph's maximum node degree must match. Stores `adata.uns['sepal_score']` or returns a DataFrame.

## Niche Labels

### `sq.gr.calculate_niche`

```python
sq.gr.calculate_niche(
    data,
    flavor,
    library_key=None,
    mask=None,
    groups=None,
    n_neighbors=None,
    resolutions=None,
    min_niche_size=None,
    scale=True,
    abs_nhood=False,
    distance=None,
    n_hop_weights=None,
    aggregation=None,
    n_components=None,
    random_state=42,
    spatial_connectivities_key="spatial_connectivities",
    latent_connectivities_key="connectivities",
    layer_ratio=1.0,
    n_iterations=-1,
    use_weights=True,
    use_rep=None,
    inplace=True,
    *,
    table_key=None,
)
```

Available `flavor` values are `"neighborhood"`, `"utag"`, `"cellcharter"`, and `"spatialleiden"`. A spatial graph is required. `spatialleiden` also requires a latent graph, usually from Scanpy, in `latent_connectivities_key`; the optional `squidpy[leiden]` dependencies provide `leidenalg` and `spatialleiden` for Leiden-backed niche workflows. With `inplace=True`, labels are written to `adata.obs` or the selected `SpatialData` table.

## SpatialData Table Rules

Most `squidpy.gr` functions call an internal resolver: if the input is `SpatialData`, `table_key` is required and must name an existing table. Missing `table_key` raises a required-argument error; an unknown key raises a value error listing available tables. For graph construction from elements, ensure `elements_to_coordinate_systems` maps every relevant element to its coordinate system and that the table annotates those element instances.
