---
name: plotting-reporting
description: "Use for Scanpy sc.pl plotting, figure saving, headless rendering,
  embedding/spatial/gene/QC/marker plots, Matplotlib object handling, palettes,
  and plotting troubleshooting after analysis outputs already exist in AnnData."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Scanpy Plotting and Reporting

Use this sub-skill when a task is about rendering or exporting Scanpy figures from an existing `anndata.AnnData` object. It covers `scanpy.pl` APIs, figure settings, Matplotlib return objects, non-interactive execution, and common failures around colors, genes, raw/layers, spatial metadata, and saved paths.

## Route by task

- **Embedding and scatter panels**: Use `references/plotting-workflows.md` for `sc.pl.embedding`, `sc.pl.umap`, `sc.pl.tsne`, `sc.pl.pca`, `sc.pl.spatial`, color keys, `groups`, `mask_obs`, `gene_symbols`, `layer`, `use_raw`, palettes, legends, axes, and multi-panel behavior.
- **Grouped marker summaries**: Use `references/plotting-workflows.md` for `sc.pl.dotplot`, `sc.pl.matrixplot`, `sc.pl.stacked_violin`, `sc.pl.heatmap`, `sc.pl.tracksplot`, `sc.pl.dendrogram`, and `DotPlot`/`MatrixPlot`/`StackedViolin` customization.
- **Rank-gene and QC reports**: Use `references/plotting-workflows.md` for `sc.pl.rank_genes_groups*`, `sc.pl.highly_variable_genes`, `sc.pl.highest_expr_genes`, `sc.pl.violin`, PCA variance/loadings, and other reports that visualize precomputed annotations.
- **Saving, CI, and publication defaults**: Use `references/figure-settings.md` for `matplotlib.use("Agg")`, `show=False`, `return_fig`, `ax`, explicit `figure.savefig`, `sc.settings.figdir`, `sc.settings.autoshow`, `sc.settings.autosave`, and `sc.set_figure_params`.
- **Failure diagnosis**: Use `references/troubleshooting.md` for missing `.obsm` bases, missing `.obs`/gene color keys, `.raw` versus `.layers`, categorical palettes, spatial image metadata, backend/display errors, and `save=` surprises.

## Safe default workflow

1. Verify the plotted state already exists in `adata`: coordinates in `.obsm`, annotations in `.obs`, genes in the selected expression source, marker results in `.uns`, layers in `.layers`, spatial metadata in `.uns['spatial']`, or categorical colors in `.uns`.
2. In scripts, tests, servers, and CI, set the Matplotlib backend to `Agg` before importing `matplotlib.pyplot`, set `sc.settings.autoshow = False`, and pass `show=False` to every plotting call.
3. Prefer explicit saves from returned objects: `ax = sc.pl.umap(adata, color='cluster', show=False)` followed by `ax.figure.savefig(path, dpi=200, bbox_inches='tight')`.
4. For class-backed grouped plots, pass `return_fig=True`, style the returned `DotPlot`, `MatrixPlot`, or `StackedViolin` object, call `make_figure()` when needed, then save `plot.fig`.
5. Close figures after saving in loops with `matplotlib.pyplot.close(fig)` or `plt.close('all')` to avoid memory growth and accidental figure reuse.

## Bundled helper

- `scripts/scanpy_headless_plot_smoke.py` creates a tiny synthetic `AnnData`, uses the `Agg` backend, renders UMAP/embedding/PCA and optional dotplot outputs with `show=False`, saves PNGs, and prints JSON. Use it as a minimal headless plotting smoke test without relying on repository files.

## Boundaries

- Do **not** compute upstream analysis artifacts here. Route PCA, neighbors, UMAP, clustering, PAGA, dendrogram creation, and rank-gene computation to graph/embedding or analysis sub-skills.
- Do **not** cover preprocessing/QC metric creation here. This sub-skill only plots those outputs when already present.
- Do **not** route optional external plotting such as PHATE, TriMap, SAM, Wishbone, or Squidpy-specific spatial plotting here; use external integration guidance when the user explicitly needs those APIs.
- Do **not** make public instructions depend on local checkout paths, repository tests, generated docs, or private output directories.
