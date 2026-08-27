# Visualization API Reference

This reference lists the plotting APIs this sub-skill owns, their live inspected signatures in compact form, and the keys they expect. Use it with `plotting-workflows.md` for examples.

## Spatial Plotters

### `sq.pl.spatial_scatter`

Purpose: plot spatial coordinates as spots/cells, optionally over images and graph edges.

Compact signature:

```python
sq.pl.spatial_scatter(
    adata,
    shape=None,
    color=None,
    groups=None,
    library_id=None,
    library_key=None,
    spatial_key="spatial",
    img=True,
    img_res_key="hires",
    img_alpha=None,
    img_cmap=None,
    img_channel=None,
    use_raw=None,
    layer=None,
    alt_var=None,
    size=None,
    size_key="spot_diameter_fullres",
    scale_factor=None,
    crop_coord=None,
    cmap=None,
    palette=None,
    alpha=1.0,
    norm=None,
    na_color=(0, 0, 0, 0),
    connectivity_key=None,
    edges_width=1.0,
    edges_color="grey",
    library_first=True,
    frameon=None,
    wspace=None,
    hspace=0.25,
    ncols=4,
    outline=False,
    legend_loc="right margin",
    colorbar=True,
    scalebar_dx=None,
    scalebar_units=None,
    title=None,
    axis_label=None,
    fig=None,
    ax=None,
    return_ax=False,
    figsize=None,
    dpi=None,
    save=None,
    scalebar_kwargs={},
    edges_kwargs={},
    **kwargs,
)
```

Important storage keys:

- Coordinates: `adata.obsm[spatial_key]`, default `adata.obsm['spatial']`.
- Image metadata: `adata.uns['spatial'][library_id]['images'][img_res_key]` when `img=True` and no array is passed directly.
- Scalefactors: `adata.uns['spatial'][library_id]['scalefactors']` for automatic scaling and spot size.
- Graph edges: `adata.obsp[connectivity_key]` when `connectivity_key` is supplied.

### `sq.pl.spatial_segment`

Purpose: plot segmentation mask regions linked to AnnData observations, optionally over an image.

Compact signature differences from `spatial_scatter`:

```python
sq.pl.spatial_segment(
    adata,
    color=None,
    groups=None,
    library_id=None,
    library_key=None,
    spatial_key="spatial",
    img=True,
    img_res_key="hires",
    seg=None,
    seg_key="segmentation",
    seg_cell_id=None,
    seg_contourpx=None,
    seg_outline=False,
    crop_coord=None,
    connectivity_key=None,
    return_ax=False,
    save=None,
    **kwargs,
)
```

Important storage keys:

- Cell ids: `adata.obs[seg_cell_id]` must exist and contain integer labels matching the segmentation image.
- Segmentation: pass `seg=<array>` or store under `adata.uns['spatial'][library_id]['images'][seg_key]`.
- Library routing: `library_key` is required when plotting multiple libraries or segmentation cell ids by library.

## Graph and Statistic Plotters

All graph/statistic plotters require categorical `adata.obs[cluster_key]` and precomputed results.

| Plotter | Required precompute | Main stored result | Key plotting options |
| --- | --- | --- | --- |
| `sq.pl.nhood_enrichment(adata, cluster_key, mode="zscore")` | `sq.gr.nhood_enrichment` | `adata.uns[f"{cluster_key}_nhood_enrichment"]` | `mode`, `annotate`, `method`, `cmap`, `palette`, `ax`, `save` |
| `sq.pl.centrality_scores(adata, cluster_key, score=None)` | `sq.gr.centrality_scores` | `adata.uns[f"{cluster_key}_centrality_scores"]` | `score`, `legend_kwargs`, `palette`, `figsize`, `save` |
| `sq.pl.interaction_matrix(adata, cluster_key)` | `sq.gr.interaction_matrix` | `adata.uns[f"{cluster_key}_interactions"]` | `annotate`, `method`, `cmap`, `palette`, `ax`, `save` |
| `sq.pl.co_occurrence(adata, cluster_key, clusters=None)` | `sq.gr.co_occurrence` | `adata.uns[f"{cluster_key}_co_occurrence"]` | `clusters`, `palette`, `legend_kwargs`, `save` |
| `sq.pl.ripley(adata, cluster_key, mode="F")` | `sq.gr.ripley` with same mode | `adata.uns[f"{cluster_key}_ripley_{mode}"]` | `mode`, `plot_sims`, `palette`, `ax`, `save` |

If a stored result is absent, Squidpy raises a `KeyError` instructing the caller to run the matching `squidpy.gr.<function>(..., cluster_key=...)` first.

## Ligand-Receptor Plotter

Purpose: plot the result of `sq.gr.ligrec` as a Scanpy-style dot plot.

Compact signature:

```python
sq.pl.ligrec(
    adata_or_result,
    cluster_key=None,
    source_groups=None,
    target_groups=None,
    means_range=(-float("inf"), float("inf")),
    pvalue_threshold=1.0,
    remove_empty_interactions=True,
    remove_nonsig_interactions=False,
    dendrogram=None,
    alpha=0.001,
    swap_axes=False,
    title=None,
    figsize=None,
    dpi=None,
    save=None,
    **kwargs,
)
```

Inputs:

- AnnData input requires `cluster_key` and stored `adata.uns[f"{cluster_key}_ligrec"]`.
- Mapping input should contain at least `"means"` and `"pvalues"` DataFrames with interaction rows and source/target cluster columns.
- `source_groups` and `target_groups` select cluster combinations from the result columns.
- `kwargs` are forwarded to `scanpy.pl.DotPlot.style` or `.legend` after Squidpy filters unsupported arguments.

## Tool and Helper Plotters

### `sq.pl.var_by_distance`

Purpose: plot variables against distance-to-anchor columns in a design matrix.

Compact signature:

```python
sq.pl.var_by_distance(
    adata,
    var,
    anchor_key,
    design_matrix_key="design_matrix",
    stack_vars=False,
    covariate=None,
    order=5,
    show_scatter=True,
    color=None,
    line_palette=None,
    scatter_palette="viridis",
    dpi=None,
    figsize=None,
    save=None,
    title=None,
    axis_label=None,
    return_ax=None,
    regplot_kwargs={},
    scatterplot_kwargs={},
)
```

Inputs:

- `adata.obsm[design_matrix_key]` is the design matrix from `sq.tl.var_by_distance`.
- `var` can name genes in `adata.var_names` or columns in `adata.obs`.
- `anchor_key` names one or more distance columns in the design matrix.
- `covariate` requests separate regression lines; do not combine it with `stack_vars=True`.

### `sq.pl.extract`

Purpose: copy feature columns from `adata.obsm` to `.obs` in a temporary AnnData object for Scanpy plotting.

Signature:

```python
sq.pl.extract(adata, obsm_key="img_features", prefix=None)
```

Behavior:

- Accepts a single key or list of keys.
- Preserves DataFrame column names and uses numeric indices for ndarray columns.
- Applies optional prefixes and returns a copy, not an in-place mutation of the source AnnData.
- Overwrites same-named columns only in the temporary copy, with a warning.

## Matplotlib and Save Semantics

- `return_ax=True` is available on spatial plotters and `var_by_distance`; graph heatmaps usually use `ax` instead.
- `save` delegates to Squidpy's `save_fig`; extensionless names default to PNG and relative paths are resolved through Scanpy figure settings.
- `dpi`, `figsize`, palette, colormap, and legend options are Matplotlib/Seaborn-facing and may affect visual-regression baselines across Matplotlib versions.
