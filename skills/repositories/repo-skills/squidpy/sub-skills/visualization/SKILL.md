---
name: visualization
description: "Render Squidpy plots for spatial overlays, segmentation, graph
  statistics, ligand-receptor heatmaps, and variation-by-distance results."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Squidpy Visualization

Use this sub-skill when a task is about rendering Squidpy figures after the AnnData or SpatialData-like table is already loaded and, when needed, analysis results have already been computed.

## Route

- Spatial overlays and segmentation masks: read `references/plotting-workflows.md#spatial-overlays` and `references/api-reference.md#spatial-plotters`.
- Neighborhood, centrality, interaction, co-occurrence, Ripley, or ligand-receptor plots: read `references/plotting-workflows.md#graph-and-statistic-plots`.
- Distance-to-anchor plots and image-feature extraction for plotting: read `references/plotting-workflows.md#tool-and-feature-plotting`.
- Plotting failures, headless rendering, palette mismatches, saved files, or visual-regression differences: read `references/troubleshooting.md`.
- Smoke-test a plotting installation without downloads or repository fixtures: run `python scripts/plotting_smoke.py --quiet`.

## Boundaries

- This sub-skill renders figures with `squidpy.pl`; it does not compute graph statistics, ligand-receptor tests, or distance design matrices.
- Route graph construction and statistic computation to `../graph-analysis/SKILL.md` before plotting graph outputs.
- Route design-matrix creation for `sq.pl.var_by_distance` to `../tools-workflows/SKILL.md`.
- Route data loading, Visium metadata repair, missing `.obsm['spatial']`, or missing `.uns['spatial']` image metadata to `../datasets-and-io/SKILL.md`.
- Route stable `ImageContainer` processing to `../image-analysis/SKILL.md` and experimental QC or tiling plots to `../experimental-imaging/SKILL.md`.

## Practical Defaults

- Use `matplotlib.use("Agg")` before importing `pyplot` in headless scripts.
- Prefer `return_ax=True` for `sq.pl.spatial_scatter`, `sq.pl.spatial_segment`, and `sq.pl.var_by_distance` when the caller needs axes.
- For graph/statistic plotters, compute the corresponding `sq.gr.*` result first and treat plot functions as renderers over stored keys.
- For image overlays, verify `library_id`, `library_key`, `img_res_key`, scalefactors, and segmentation cell IDs before tuning aesthetics.
