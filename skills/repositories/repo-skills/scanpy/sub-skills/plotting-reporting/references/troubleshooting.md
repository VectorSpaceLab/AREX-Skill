# Plotting Troubleshooting

Diagnose Scanpy plotting failures by checking the expected `AnnData` state and display environment first. Do not recompute upstream analysis inside the plotting step unless the user explicitly routes that work to an analysis sub-skill.

## Headless or CI failures

Symptoms:

- Errors mention a display, GUI framework, or Matplotlib backend.
- Plot calls hang, open windows, or produce blank saved files during automation.
- Figures are shown or closed before saving.

Fixes:

1. Set the backend before importing `pyplot`:
   ```python
   import matplotlib
   matplotlib.use("Agg")
   import matplotlib.pyplot as plt
   ```
2. Set `sc.settings.autoshow = False` and pass `show=False` to each plot call.
3. Save from returned objects with `figure.savefig(...)`.
4. Close figures after saving to prevent memory buildup.
5. Run `scripts/scanpy_headless_plot_smoke.py --output-dir /tmp/scanpy-plot-smoke` as a minimal plotting check.
6. If the smoke script prints `{"error": "missing_dependency"}`, install or activate an environment containing `scanpy`, `anndata`, `matplotlib`, `numpy`, and `pandas` before debugging plotting code.

## Missing embedding basis

Symptoms:

- `KeyError` or a message says a basis such as `umap`, `pca`, `tsne`, or `spatial` is missing.
- `sc.pl.umap` fails even though the requested `color` key exists.

Checks and fixes:

- Confirm `adata.obsm` contains the coordinate matrix: usually `X_umap` for `sc.pl.umap`, `X_pca` for `sc.pl.pca`, `X_tsne` for `sc.pl.tsne`, and `spatial` for `sc.pl.spatial`.
- For `sc.pl.embedding(adata, basis='custom')`, prepare or load `adata.obsm['X_custom']` first.
- Route PCA, neighbors, UMAP, t-SNE, graph drawing, or spatial coordinate creation upstream.
- If only coordinate plotting is needed for spatial data without an image, use `sc.pl.spatial(..., img_key=None, spot_size=...)` or generic embedding behavior with the correct basis.

## Color key, gene symbol, raw, and layer confusion

Symptoms:

- Requested `color`, `keys`, or `var_names` are reported missing.
- A gene appears in `adata.var` but not in the plotted expression source.
- Values do not match the expected normalized, logged, raw, or layer matrix.

Checks and fixes:

- Determine whether the requested key should come from `adata.obs`, `adata.var_names`, `adata.raw.var_names`, a `.var` gene-symbol column, or a layer.
- If users provide display symbols, pass `gene_symbols='<var-column>'` and ensure the symbols map to the intended features.
- If `.raw` exists, many expression plots default to raw when `layer` is not set. Use `use_raw=False` to force `.X`.
- If plotting a layer, pass `layer='<layer-name>'` and do not pass `use_raw=True`.
- For marker summary plots, verify every gene in `var_names` exists in the selected expression source or symbol mapping.

## Categorical order and palette problems

Symptoms:

- Category colors change across figures.
- Categories appear in an unexpected order.
- Warnings mention invalid colors in `adata.uns['<key>_colors']`.
- Some categories fall back to default colors.

Checks and fixes:

- Convert the grouping column to categorical and set category order explicitly:
  ```python
  adata.obs["cluster"] = adata.obs["cluster"].astype("category")
  adata.obs["cluster"] = adata.obs["cluster"].cat.reorder_categories(["A", "B", "C"])
  ```
- Pass `palette=[...]` to embedding plots or set `adata.uns['cluster_colors']` to valid Matplotlib colors in category order.
- For grouped summaries, use `categories_order` or `order` and ensure every provided category exactly matches the data.
- If Scanpy warns about invalid colors, replace misspelled names or non-Matplotlib color names with valid names or hex colors.

## Multi-panel and axes errors

Symptoms:

- Error says `ax` cannot be specified for multiple panels.
- The return value is a list, dict, or grid instead of a single `Axes`.
- A script calls `ax.figure` but `ax` is a list.

Checks and fixes:

- Passing a list to `color` or multiple component pairs creates multiple panels; do not pass `ax`.
- Handle return types explicitly:
  ```python
  axes = sc.pl.umap(adata, color=["cluster", "GeneA"], show=False)
  fig = axes[0].figure if isinstance(axes, list) else axes.figure
  ```
- For dotplot, matrixplot, or stacked violin customization, pass `return_fig=True` and use the returned Scanpy plot object.
- For a plot embedded in a larger Matplotlib layout, use a single `color` key and a single panel.

## `save=` and `figdir` surprises

Symptoms:

- A figure is saved in `figures/` instead of the requested directory.
- The filename has an unexpected plot prefix or suffix.
- A warning mentions `save` behavior.

Checks and fixes:

- `save=` uses Scanpy-managed filenames under `sc.settings.figdir`, with a plot-specific prefix and `sc.settings.plot_suffix`.
- If `save` is a string ending in `.svg`, `.pdf`, or `.png`, Scanpy uses that extension and appends the rest to its write key.
- For exact paths, use `show=False` and `figure.savefig(output_path, ...)` instead of `save=`.
- If maintaining legacy `save=`, set `sc.settings.figdir`, `sc.settings.file_format_figs`, and `sc.settings.plot_suffix` explicitly.

## Spatial metadata and image problems

Symptoms:

- `sc.pl.spatial` fails with missing `spot_size`, `scale_factor`, `library_id`, image, or spatial metadata.
- Points are flipped, cropped incorrectly, invisible, or mismatched with the image.
- Missing values are transparent over images but gray elsewhere.

Checks and fixes:

- Confirm coordinates exist in `adata.obsm['spatial']`.
- For Visium-style data, inspect `adata.uns['spatial']` for the correct `library_id`, `images`, and `scalefactors`.
- If metadata is missing, pass `img`, `scale_factor`, and `spot_size` directly; for coordinates only, set `img_key=None` and pass `spot_size`.
- Use `crop_coord=(left, right, top, bottom)` and remember image coordinates usually have origin at the top left.
- Set `na_color` explicitly when missing-value appearance must be stable across image and no-image plots.

## Marker ranking plot failures

Symptoms:

- `sc.pl.rank_genes_groups*` fails because `rank_genes_groups` is missing.
- Groups, marker names, or symbol mappings do not match the ranking result.

Checks and fixes:

- Verify the expected key exists in `.uns`: `key in adata.uns`, defaulting to `key='rank_genes_groups'`.
- Use `sc.get.rank_genes_groups_df` outside plotting when tabular inspection is needed.
- Route `sc.tl.rank_genes_groups` computation upstream; plotting should consume existing results.
- Use plain `dotplot`, `matrixplot`, `heatmap`, `tracksplot`, or `stacked_violin` when users provide marker lists rather than a precomputed ranking.

## Dense data or slow rendering

Symptoms:

- Plotting is slow or memory-heavy.
- Vector exports become very large.
- Violin strip points obscure distributions.

Fixes:

- Reduce point size, mask/subset observations upstream, or create targeted panels instead of plotting every cell repeatedly.
- Use `sc.set_figure_params(vector_friendly=True)` for dense scatter vector exports.
- For `sc.pl.violin`, set `stripplot=False` or reduce `size`.
- Close figures in loops and avoid retaining axes lists longer than needed.
- Prefer PNG for very dense embedding panels unless vector output is required.
