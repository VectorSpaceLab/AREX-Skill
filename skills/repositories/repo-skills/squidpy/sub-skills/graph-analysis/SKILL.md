---
name: graph-analysis
description: "Build Squidpy spatial neighbor graphs and run graph/statistical
  analyses on AnnData or SpatialData tables."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Squidpy Graph Analysis

Use this sub-skill when a task needs `squidpy.gr` graph construction or graph/statistical analysis on an `AnnData` object or a `SpatialData` table: spatial neighbors, custom builders, neighborhood enrichment, co-occurrence, Ripley statistics, spatial autocorrelation, ligand-receptor testing, centrality, interaction matrices, niche labels, Sepal scores, or graph masking.

## Route First

- Need data readers, downloadable examples, Visium/Vizgen/Nanostring layouts, or `.obsm['spatial']` validation? Use `datasets-and-io` first.
- Need plots such as `sq.pl.nhood_enrichment`, `sq.pl.co_occurrence`, `sq.pl.ripley`, `sq.pl.centrality_scores`, `sq.pl.interaction_matrix`, `sq.pl.ligrec`, or graph edges in `spatial_scatter`? Compute here, then route plotting to `visualization` with the result keys.
- Need `squidpy.tl.var_by_distance`, `squidpy.tl.sliding_window`, or `sq.pl.var_by_distance`? Use `tools-workflows`.
- Need stable image processing or experimental SpatialData image tiling/QC? Use `image-analysis` or `experimental-imaging`.

## Fast Workflow

1. Prepare an `AnnData` table with coordinates in `adata.obsm['spatial']` and categorical labels in `adata.obs[cluster_key]`; for `SpatialData`, pass `table_key` to graph/statistical functions and `elements_to_coordinate_systems` when graph coordinates come from shapes or labels.
2. Build a graph with a mode-specific constructor: `sq.gr.spatial_neighbors_knn`, `sq.gr.spatial_neighbors_radius`, `sq.gr.spatial_neighbors_delaunay`, `sq.gr.spatial_neighbors_grid`, or `sq.gr.spatial_neighbors_from_builder`.
3. Avoid new code that depends on deprecated `sq.gr.spatial_neighbors`; keep it only for legacy snippets and prefer explicit mode-specific functions.
4. Confirm graph outputs exist at `adata.obsp['spatial_connectivities']`, `adata.obsp['spatial_distances']`, and `adata.uns['spatial']` unless `key_added` changed the prefix.
5. Run graph statistics with matching `connectivity_key`, `spatial_key`, `cluster_key`, and `table_key` values.
6. Validate outputs before plotting or downstream use.

## What To Read

- `references/graph-workflows.md` for graph construction choices, result keys, analysis ordering, SpatialData table handling, and validation snippets.
- `references/api-reference.md` for focused signatures, preconditions, outputs, and storage locations.
- `references/custom-builders.md` for `GraphBuilder`/`GraphBuilderCSR` contracts, built-in builders, postprocessors, and a custom approximate KNN pattern.
- `references/troubleshooting.md` for categorical labels, connectivity keys, deprecated `spatial_neighbors`, multi-library graphs, SpatialData `table_key`, ligand-receptor schema, optional niche dependencies, permutation cost, and parallel backends.
- `scripts/graph_smoke.py` for a tiny deterministic AnnData graph/statistics smoke that performs no downloads.
