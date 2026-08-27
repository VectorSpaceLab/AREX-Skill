# Graph Troubleshooting

## `cluster_key` Missing Or Not Categorical

Symptoms include errors like `Cluster key ... not found` or `Expected adata.obs[...] to be categorical` from `nhood_enrichment`, `centrality_scores`, `interaction_matrix`, `co_occurrence`, `ripley`, or `ligrec`.

Fix:

```python
cluster_key = "cell_type"
assert cluster_key in adata.obs
adata.obs[cluster_key] = adata.obs[cluster_key].astype("category")
assert len(adata.obs[cluster_key].cat.categories) >= 2
```

`ligrec` requires at least two categories. `library_key` must also be categorical when used by graph construction or neighborhood enrichment.

## Missing Or Wrong Connectivity Key

Symptoms include `Spatial connectivity key ... not found in adata.obsp` after graph construction.

Check storage:

```python
print(adata.obsp.keys())
print(adata.uns.get("spatial", {}))
```

Default graph outputs are `spatial_connectivities` and `spatial_distances`. If you used `key_added="custom"`, pass the matching key into downstream functions:

```python
sq.gr.nhood_enrichment(adata, "cell_type", connectivity_key="custom")
sq.gr.spatial_autocorr(adata, connectivity_key="custom_connectivities", genes=["GeneA"])
```

Some functions transform a prefix such as `"custom"` into `"custom_connectivities"`; others default to the full key `"spatial_connectivities"`. When unsure, pass the exact key shown in `adata.obsp` or stored in `adata.uns[key_added]['connectivities_key']`.

## Deprecated `spatial_neighbors`

The compatibility function `sq.gr.spatial_neighbors` is deprecated in the inspected API version and will be removed in a future Squidpy release. It also has legacy precedence rules: `n_neighs` is ignored when `radius` is set or `delaunay=True`, grid mode ignores `radius`, and Delaunay treats `radius` only as post-construction pruning.

Prefer explicit mode-specific calls:

```python
sq.gr.spatial_neighbors_knn(adata, n_neighs=6)
sq.gr.spatial_neighbors_radius(adata, radius=50.0)
sq.gr.spatial_neighbors_delaunay(adata)
sq.gr.spatial_neighbors_grid(adata, n_neighs=6, n_rings=1)
```

## Multi-Library Graphs

Use `library_key` when observations from multiple tissue sections, fields of view, or samples should not connect across libraries.

```python
adata.obs["library_id"] = adata.obs["library_id"].astype("category")
sq.gr.spatial_neighbors_knn(adata, library_key="library_id", n_neighs=6)
```

Common issues:

- `library_key` is not categorical.
- One library has too few observations for the selected `n_neighs` or graph mode.
- A custom builder inherited `GraphBuilder` but did not implement `combine`; use `GraphBuilderCSR`, subset by library, or implement `combine`.
- Downstream statistics are interpreted globally even though the graph has block-diagonal library structure; include `library_key` where the statistic supports it, such as `nhood_enrichment`.

## SpatialData Requires `table_key`

Most graph APIs accept `SpatialData`, but they resolve it to one `AnnData` table. Always pass `table_key="..."`. Missing `table_key` raises a required-argument error; an unknown key raises an error with available tables.

For graph construction from `SpatialData` shapes or labels, also pass `elements_to_coordinate_systems`:

```python
sq.gr.spatial_neighbors_knn(
    sdata,
    table_key="table",
    elements_to_coordinate_systems={"cells": "global"},
)
```

The table must annotate the selected element instances and order them consistently enough for Squidpy to attach centroids to the table. If coordinates already exist in `sdata.tables[table_key].obsm['spatial']`, calling graph functions on that table directly can be simpler.

## Spatial Basis Missing

Graph builders, `co_occurrence`, `ripley`, and `sepal` need coordinates in `adata.obsm[spatial_key]`.

```python
assert "spatial" in adata.obsm
assert adata.obsm["spatial"].shape[0] == adata.n_obs
assert adata.obsm["spatial"].shape[1] >= 2
```

Route data loading/layout repair to `datasets-and-io` if the coordinates or Visium metadata are absent.

## `.raw`, Gene Names, And `gene_symbols`

`ligrec` defaults to `use_raw=True`. If `adata.raw` is missing, set `use_raw=False` or populate `.raw` intentionally.

```python
sq.gr.ligrec(adata, "cell_type", interactions=interactions, use_raw=False)
```

If interaction names match a column in `adata.var` instead of `adata.var_names`, pass `gene_symbols="symbol_column"`. If interactions are filtered to zero rows, check case sensitivity, symbol aliases, complexes, and whether `use_raw` points at a different gene index.

`spatial_autocorr` with `use_raw=True` also needs requested genes in `adata.raw.var_names`. With `attr="obsm"`, `layer` must name an `.obsm` key and `genes` is interpreted as component indices.

## Ligand-Receptor Interaction Schema

Valid `interactions` inputs must resolve to source-target pairs:

```python
interactions = pd.DataFrame({"source": ["LIG"], "target": ["REC"]})
```

Common failures:

- Missing `source` or `target` columns.
- Tuple/list interactions not length 2.
- All interaction genes absent from the expression matrix selected by `use_raw` and `gene_symbols`.
- Invalid `complex_policy`; use `"min"` or `"all"`.
- Invalid `corr_axis`; use `"clusters"` or `"interactions"` when `corr_method` is set.
- Invalid `clusters` in extra keyword arguments; names must match `cluster_key` categories, or pass explicit `(source_cluster, target_cluster)` pairs when supported by the call.

Omitting `interactions` fetches from OmniPath and may fail offline. For deterministic agent workflows, provide a small explicit interaction table.

## Permutations, `n_jobs`, And Backends

Permutation-heavy functions can be expensive:

- `nhood_enrichment(n_perms=1000)` permutes cluster labels.
- `spatial_autocorr(n_perms=...)` permutes feature scores; `n_perms=None` uses analytic p-values only.
- `ripley(n_simulations=100, n_observations=1000)` simulates point processes.
- `ligrec(n_perms=1000)` can be large over many interactions and cluster pairs.

For quick validation, lower permutation/simulation counts and set seeds:

```python
sq.gr.nhood_enrichment(adata, "cell_type", n_perms=20, seed=0, n_jobs=1, show_progress_bar=False)
sq.gr.spatial_autocorr(adata, genes=["GeneA"], n_perms=None, n_jobs=1, show_progress_bar=False)
```

`backend` is passed to Squidpy's parallel helper for several statistics; common values include `"loky"`, `"threading"`, and `"multiprocessing"`. If multiprocessing has pickling, memory, or notebook issues, retry with `n_jobs=1` or `backend="threading"`.

## Sepal Degree Mismatch

`sepal` validates `max_neighs` against the maximum degree of the graph. If it raises a degree mismatch, rebuild a grid graph with the expected topology or switch to `spatial_autocorr` for less grid-specific spatial variability scoring.

```python
sq.gr.spatial_neighbors_grid(adata, n_neighs=6, n_rings=1)
sq.gr.sepal(adata, max_neighs=6)
```

## Niche Preconditions And Optional Dependencies

`calculate_niche` always needs `spatial_connectivities_key` in `.obsp`. Flavor-specific failure modes:

- `neighborhood`: requires a valid `groups` column and sensible `n_neighbors`/`resolutions`.
- `utag`: uses adjacency-smoothed expression features and Leiden-style clustering through Scanpy.
- `cellcharter`: can densify or aggregate matrices and may be memory-heavy on large tables.
- `spatialleiden`: requires both a spatial graph and latent graph, usually `adata.obsp['connectivities']` from `scanpy.pp.neighbors`; install optional Leiden support with `squidpy[leiden]` when `spatialleiden` or `leidenalg` is missing.

If `SpatialData` is used with `inplace=True`, Squidpy updates `sdata.tables[table_key]`; verify the table after the call.

## Graph Masking Pitfalls

`mask_graph` only accepts Shapely `Polygon` or `MultiPolygon`. The polygon must be in the same coordinate system as the graph; Squidpy does not verify coordinate-system compatibility. It removes or keeps edges based on the full line segment connecting two observations, not on node membership alone.

Use `negative_mask=True` only when you want to remove fully contained edges and keep the rest. Masked keys are prefixed as `f'{key_added}_{spatial_key}_...'`, so downstream calls must use the masked connectivity key explicitly.
