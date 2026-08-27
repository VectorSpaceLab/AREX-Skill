# Plotting Workflows

Squidpy plotting is mostly a rendering layer over AnnData fields and results stored by `squidpy.gr`, `squidpy.tl`, or `squidpy.im`. Build or validate those inputs first, then call `squidpy.pl` with explicit keys.

## Spatial Overlays

Use `sq.pl.spatial_scatter` for spots or cells and `sq.pl.spatial_segment` when segmentation masks should color cell regions.

### Minimal No-Image Scatter

```python
import matplotlib
matplotlib.use("Agg")

import squidpy as sq

ax = sq.pl.spatial_scatter(
    adata,
    shape=None,
    img=False,
    color="cell_type",
    spatial_key="spatial",
    size=30,
    return_ax=True,
)
ax.figure.savefig("spatial_scatter.png", dpi=150, bbox_inches="tight")
```

This only needs `adata.obsm['spatial']` and the requested `color` column or gene. It is the safest fallback when `.uns['spatial']` image metadata is absent.

### Image-Backed Visium-Style Overlay

```python
ax = sq.pl.spatial_scatter(
    adata,
    color=["cluster", "GeneA"],
    library_id="sampleA",
    library_key="library_id",
    img=True,
    img_res_key="hires",
    size=1.0,
    crop_coord=(0, 0, 2500, 2500),
    scalebar_dx=2.0,
    scalebar_units="um",
    return_ax=True,
)
```

Check these prerequisites before plotting:

- `adata.obsm['spatial']` contains pixel-space coordinates.
- `adata.uns['spatial'][library_id]['images'][img_res_key]` exists when `img=True`.
- `adata.uns['spatial'][library_id]['scalefactors']` includes the matching image scale and `spot_diameter_fullres` when relying on automatic sizing.
- `adata.obs[library_key]` is categorical and contains each requested `library_id` for multi-library plots.
- `crop_coord` uses image-coordinate order `(x0, y0, x1, y1)` and can be a list matching the selected libraries.

### Cropped Scatter With Graph Edges But No Image

```python
sq.pl.spatial_scatter(
    adata,
    shape="circle",
    img=False,
    color="cluster",
    groups=["T cell", "B cell"],
    connectivity_key="spatial_connectivities",
    edges_width=0.3,
    edges_color="lightgrey",
    crop_coord=(100, 100, 900, 900),
    size=20,
    legend_loc="right margin",
    return_ax=True,
)
```

Compute or load `adata.obsp['spatial_connectivities']` first, typically through graph-analysis. If no image is plotted, point size is Matplotlib scatter size rather than Visium spot diameter in image pixels.

### Segmentation Overlay

```python
sq.pl.spatial_segment(
    adata,
    color="Cluster",
    groups=["Fibroblast", "Endothelial"],
    library_key="library_id",
    library_id="sampleA",
    seg=True,
    seg_key="segmentation",
    seg_cell_id="cell_id",
    img=True,
    img_alpha=0.5,
    seg_outline=True,
    seg_contourpx=15,
    return_ax=True,
)
```

`spatial_segment` requires an integer cell-id column in `adata.obs[seg_cell_id]` and a segmentation array either passed directly as `seg=<array>` or stored under the selected library's image metadata. Use `img=False, seg=True` for mask-only categorical plots.

## Graph and Statistic Plots

Graph/statistic plotters read results stored by matching `sq.gr.*` functions. Do not expect `sq.pl.*` calls to compute missing results.

```python
import squidpy as sq

sq.gr.spatial_neighbors_knn(adata, n_neighs=6, key_added="spatial")
sq.gr.nhood_enrichment(adata, cluster_key="cluster", connectivity_key="spatial_connectivities", n_perms=100)
sq.pl.nhood_enrichment(adata, cluster_key="cluster", mode="zscore", annotate=True, cmap="magma")
```

Common render flows:

- `sq.gr.nhood_enrichment(..., cluster_key=...)` then `sq.pl.nhood_enrichment(..., mode="zscore" | "count")`.
- `sq.gr.centrality_scores(..., cluster_key=...)` then `sq.pl.centrality_scores(..., score=None | "degree_centrality")`.
- `sq.gr.interaction_matrix(..., cluster_key=...)` then `sq.pl.interaction_matrix(..., annotate=True, method="single")`.
- `sq.gr.co_occurrence(..., cluster_key=...)` then `sq.pl.co_occurrence(..., clusters=[...])`.
- `sq.gr.ripley(..., cluster_key=..., mode="F" | "G" | "L")` then `sq.pl.ripley(..., mode=..., plot_sims=True)`.

All of these expect `adata.obs[cluster_key]` to be categorical. Heatmap plotters accept `ax` and `save`; line/scatter graph plotters generally create their own figures unless an `ax` parameter is present.

### Ligand-Receptor Heatmap

`sq.pl.ligrec` accepts either an AnnData with `adata.uns[f"{cluster_key}_ligrec"]` or the mapping returned by `sq.gr.ligrec`.

```python
sq.pl.ligrec(
    ligrec_result,
    source_groups=["B cell"],
    target_groups=["T cell", "Macrophage"],
    means_range=(0.2, 2.0),
    pvalue_threshold=0.05,
    remove_empty_interactions=True,
    remove_nonsig_interactions=True,
    dendrogram="interacting_molecules",
    alpha=0.05,
    swap_axes=False,
)
```

Use filtering to keep heatmaps readable:

- `means_range` keeps interactions whose mean expression is inside a closed interval.
- `pvalue_threshold` masks interactions above the threshold.
- `remove_empty_interactions=True` drops all-NaN rows or columns.
- `remove_nonsig_interactions=True` drops rows or columns with no p-values at or below `alpha`.
- `dendrogram` can be `None`, `"interacting_molecules"`, `"interacting_clusters"`, or `"both"`; clustering large dense matrices can be slow or visually crowded.

## Tool and Feature Plotting

### Variation by Distance

`sq.pl.var_by_distance` plots a design matrix already produced by `sq.tl.var_by_distance`; route design-matrix construction to tools-workflows.

```python
ax = sq.pl.var_by_distance(
    adata,
    design_matrix_key="design_matrix",
    var="GeneA",
    anchor_key="Epithelial",
    covariate="donor",
    show_scatter=False,
    line_palette=["tab:blue", "tab:orange"],
    return_ax=True,
)
```

Key checks:

- `adata.obsm[design_matrix_key]` exists and behaves like a table.
- `anchor_key` names a distance column in that design matrix.
- `var` is in `adata.var_names` or `adata.obs`.
- `covariate`, if provided, is a column in the design matrix.
- `stack_vars=True` cannot be combined with `covariate`.

### Extract Image Features for Scanpy Plots

`sq.pl.extract` creates a temporary AnnData with `adata.obsm` feature columns copied into `.obs` so regular Scanpy plotters can color by those columns.

```python
plot_adata = sq.pl.extract(adata, obsm_key="img_features", prefix="img")
# Example: sc.pl.umap(plot_adata, color="img_summary_ch-0_quantile-0.9")
```

If `obsm_key` is a DataFrame, column names are preserved with the prefix. If it is an array, numeric columns become `0`, `1`, ... with the prefix. Existing `.obs` columns with the same names are overwritten in the temporary copy.

## Saving and Axes Handling

- `save="name.png"` uses Squidpy/Scanpy figure saving conventions; relative paths may be resolved under Scanpy's figure directory.
- To control exact output paths in scripts, prefer `return_ax=True` where available and call `ax.figure.savefig(...)` yourself.
- `sq.pl.nhood_enrichment`, `sq.pl.interaction_matrix`, and `sq.pl.ripley` accept an `ax`; `sq.pl.centrality_scores`, `sq.pl.co_occurrence`, and `sq.pl.ligrec` are figure-producing helpers without `return_ax`.
- Close figures in batch scripts with `matplotlib.pyplot.close("all")` to avoid memory leaks.
