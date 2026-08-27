# Scanpy Plotting Workflows

`scanpy.pl` is the plotting/reporting layer for an existing `AnnData` object. Most plotting functions read already-computed fields and return Matplotlib axes, figures, grids, or Scanpy plot objects when display is disabled. Before plotting, inspect `adata.obs`, `adata.var_names`, `adata.raw`, `adata.layers`, `adata.obsm`, and `adata.uns` so missing analysis state is routed upstream instead of silently recomputed in reporting code.

## API map

| Need | Primary APIs | Required `AnnData` state | Notes |
| --- | --- | --- | --- |
| Embedding/scatter plots | `sc.pl.embedding`, `sc.pl.umap`, `sc.pl.tsne`, `sc.pl.pca`, `sc.pl.diffmap`, `sc.pl.draw_graph` | Coordinates in `adata.obsm`, usually `X_<basis>` | Convenience wrappers delegate to embedding-style plotting. |
| Spatial plots | `sc.pl.spatial`, `sc.pl.embedding(..., basis='spatial')` | `adata.obsm['spatial']`; optional Visium image/scalefactor metadata in `adata.uns['spatial']` | `sc.pl.spatial` remains available for Scanpy workflows; new spatial-heavy work may use external spatial tools. |
| Expression distributions | `sc.pl.violin`, `sc.pl.stacked_violin` | `.obs` keys or genes/features in the selected matrix | Use `stripplot=False` or smaller point sizes for large data. |
| Grouped summaries | `sc.pl.dotplot`, `sc.pl.matrixplot`, `sc.pl.heatmap`, `sc.pl.tracksplot` | `var_names` plus `groupby` categories | `var_names` can be a list or a dict of marker groups. |
| Plot classes | `sc.pl.DotPlot`, `sc.pl.MatrixPlot`, `sc.pl.StackedViolin` | Same state as grouped summary APIs | Best for method chaining, styling, legends, totals, dendrograms, and axes access. |
| Rank-gene reports | `sc.pl.rank_genes_groups`, `sc.pl.rank_genes_groups_violin`, `sc.pl.rank_genes_groups_dotplot`, `sc.pl.rank_genes_groups_matrixplot`, `sc.pl.rank_genes_groups_heatmap`, `sc.pl.rank_genes_groups_stacked_violin`, `sc.pl.rank_genes_groups_tracksplot` | Ranking result in `adata.uns[key]`, default `rank_genes_groups` | Plotting consumes precomputed rankings; do not run `sc.tl.rank_genes_groups` in this sub-skill. |
| QC/preprocessing reports | `sc.pl.highest_expr_genes`, `sc.pl.highly_variable_genes`, `sc.pl.scrublet_score_distribution`, `sc.pl.pca_variance_ratio`, `sc.pl.pca_loadings`, `sc.pl.pca_overview` | Corresponding QC, HVG, scrublet, or PCA outputs | These visualize outputs computed elsewhere. |
| Trajectory/graph reports | `sc.pl.paga`, `sc.pl.paga_path`, `sc.pl.paga_compare`, `sc.pl.dendrogram`, `sc.pl.correlation_matrix` | Existing PAGA, dendrogram, or grouping results | Route creation of graph and trajectory annotations upstream. |

## Embedding and scatter plots

Use `sc.pl.embedding(adata, basis, ...)` when the basis name is dynamic, and wrapper functions when the basis is known:

```python
ax = sc.pl.umap(adata, color="cluster", show=False)
ax.figure.savefig("umap_clusters.png", dpi=200, bbox_inches="tight")
```

Common embedding parameters:

| Parameter | Use |
| --- | --- |
| `color` | One key or a list of keys from `.obs`, genes/features, or color literals. Lists create multiple panels. |
| `basis` | Generic embedding basis for `sc.pl.embedding`; coordinates are usually `adata.obsm[f'X_{basis}']`. |
| `groups` | Restrict displayed categories for categorical `color`. |
| `mask_obs` | Boolean mask or `.obs` key selecting observations; do not combine with `groups`. |
| `gene_symbols` | Resolve displayed gene symbols through a column in `adata.var`. |
| `use_raw` | Defaults to `.raw` when present and `layer` is not set; set explicitly when source matters. |
| `layer` | Plot expression from `adata.layers[layer]`; cannot be combined with `use_raw=True`. |
| `sort_order` | Plot high continuous values last so they remain visible. |
| `neighbors_key`, `edges`, `arrows` | Overlay graph edges or arrows when graph data exists. |
| `components` / `dimensions` | Select non-default component pairs; do not pass both. |
| `legend_loc`, `legend_fontsize`, `legend_fontoutline` | Control categorical legends and labels. |
| `palette` | Assign categorical colors; Scanpy may also use `adata.uns[f'{key}_colors']`. |
| `cmap` / `color_map`, `vmin`, `vmax`, `vcenter`, `norm`, `na_color`, `na_in_legend` | Control continuous color scales and missing values. Avoid passing both `cmap` and `color_map`. |
| `frameon`, `title`, `ncols`, `hspace`, `wspace`, `size`, `marker` | Control layout and rendering. |
| `ax`, `show`, `return_fig` | Use `ax` only for one panel. Use `show=False` in scripts. Use `return_fig=True` for a figure object. |

Important behavior:

- `sc.pl.umap` expects `adata.obsm['X_umap']`; `sc.pl.tsne` expects `X_tsne`; `sc.pl.pca` expects `X_pca` unless PCA coordinates are otherwise prepared.
- Multiple `color` values or component pairs produce multiple panels. Do not pass `ax` for multi-panel calls.
- If `.raw` exists, expression coloring can use `.raw` by default. Choose `use_raw=False` or `layer='...'` when the plotted values must come from `.X` or a layer.
- Categorical colors are ordered by the category order. Stable plots require stable categorical ordering and palettes.

## Spatial plots

`sc.pl.spatial` plots spatial coordinates and optionally overlays them on tissue images:

```python
ax = sc.pl.spatial(
    adata,
    color="cluster",
    img_key=None,
    spot_size=50,
    show=False,
)
```

Use these checks before plotting:

- Coordinates should be present in `adata.obsm['spatial']` for `sc.pl.spatial`.
- Visium-style metadata may live under `adata.uns['spatial'][library_id]['images']` and `['scalefactors']`.
- If image metadata is absent, use `img_key=None` and pass `spot_size`, or provide `img`, `scale_factor`, and `spot_size` directly.
- Use `library_id` when multiple libraries are stored.
- Use `crop_coord=(left, right, top, bottom)`, `alpha_img`, `bw`, `size`, and `na_color` to control overlays and missing values.

## Distribution, preprocessing, and QC plots

Use `sc.pl.violin` for observation metrics or gene expression distributions:

```python
ax = sc.pl.violin(
    adata,
    keys=["n_genes_by_counts", "total_counts"],
    groupby="cluster",
    stripplot=False,
    rotation=90,
    show=False,
)
```

Guidance:

- `keys` can name `.obs` columns or genes/features.
- `groupby` groups distributions by an observation category.
- `order` controls category order and must match actual categories.
- `multi_panel=True` separates multiple keys into panels when grouped.
- `layer` takes precedence over raw defaults; set `use_raw=False` to force `.X`.
- Use `sc.pl.highly_variable_genes`, `sc.pl.highest_expr_genes`, `sc.pl.scrublet_score_distribution`, and PCA loadings/variance plots only after the corresponding values already exist.

## Grouped expression summary plots

Grouped summaries are useful for marker sets by cluster or condition:

```python
markers = {"T cells": ["CD3D", "IL7R"], "B cells": ["MS4A1", "CD79A"]}
plot = sc.pl.dotplot(
    adata,
    markers,
    groupby="cluster",
    use_raw=False,
    dendrogram=False,
    return_fig=True,
)
plot.style(cmap="Reds").legend(colorbar_title="Mean expression")
plot.make_figure()
plot.fig.savefig("marker_dotplot.png", dpi=200, bbox_inches="tight")
```

Shared concepts:

| Option | Applies to | Meaning |
| --- | --- | --- |
| `var_names` | dotplot, matrixplot, heatmap, tracksplot, stacked_violin | Gene/feature list or dict of group label to genes. |
| `groupby` | grouped APIs/classes | Observation category or categories to aggregate over. |
| `categories_order` / `order` | grouped APIs/classes | Manual category order; values must match categories. |
| `dendrogram` | grouped APIs | Reorder categories with an existing or computed dendrogram key. |
| `standard_scale` | dotplot, matrixplot, stacked_violin, heatmap | Scale by `'var'` or `'group'`. |
| `swap_axes` | dotplot, matrixplot, stacked_violin, heatmap | Put groups on x-axis and genes on y-axis. |
| `gene_symbols` | expression summary APIs/classes | Resolve names through a `.var` column. |
| `layer`, `use_raw`, `log` | expression plots | Select expression source and transformation. |
| `return_fig=True` | dotplot, matrixplot, stacked_violin | Return a Scanpy plot object for styling and saving. |

Plot class patterns:

- `DotPlot`, `MatrixPlot`, and `StackedViolin` support `.style(...)`, `.legend(...)`, `.add_dendrogram(...)`, `.add_totals()` where available, `.swap_axes()`, `.make_figure()`, `.show()`, and `.get_axes()`.
- Dotplot size represents the fraction of cells expressing a gene above `expression_cutoff`; color typically represents mean expression.
- Matrixplot values are mean expression by group unless `values_df` is supplied.
- Stacked violin wraps seaborn-style violin plots; disable strip points or reduce point size for large datasets.

## Marker ranking plots

Rank-gene plotting APIs consume `adata.uns[key]`, defaulting to `key='rank_genes_groups'`:

```python
if "rank_genes_groups" not in adata.uns:
    raise KeyError("Load or compute marker ranking results before plotting them.")
sc.pl.rank_genes_groups_dotplot(
    adata,
    key="rank_genes_groups",
    groupby="cluster",
    show=False,
)
```

Use rank-gene plots when a differential-expression result already exists. Use plain `dotplot`, `matrixplot`, `heatmap`, `tracksplot`, or `stacked_violin` when a user supplies marker lists directly.

## Plot object customization

- Single embedding axis: `ax = sc.pl.umap(..., show=False)`, then mutate `ax` and save `ax.figure`.
- Multi-panel embedding: `axes = sc.pl.umap(..., color=[...], show=False)`, get the figure from the first axes object, and do not pass `ax`.
- Class-backed grouped plot: `plot = sc.pl.dotplot(..., return_fig=True)`, chain style methods, call `make_figure()` if needed, then save `plot.fig`.
- Existing Matplotlib axes: pass `ax=ax` only when the plotting function produces one panel.
- Exact file output: prefer explicit `figure.savefig(path, ...)` over `save=` for new automated code.
