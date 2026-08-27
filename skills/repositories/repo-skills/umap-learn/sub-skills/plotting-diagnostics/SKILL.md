---
name: plotting-diagnostics
description: "Diagnose optional umap.plot static, datashaded, connectivity,
  diagnostic, hover/search, and nearest-neighbour workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Plotting Diagnostics

Use this sub-skill when you already have a fitted UMAP-family mapper and need to inspect or recover plotting workflows in `umap.plot`.

## Covers

- `points`, `connectivity`, `diagnostic`, `interactive`, `nearest_neighbour_distribution`, and `show`.
- Optional `umap.plot` import failures, dependency checks, and install advice.
- Static matplotlib, datashaded large-data, connectivity graph, Bokeh interactive, hover/search, and nearest-neighbour histogram paths.

## Route Elsewhere

- Fit, transform, update, inverse-transform, nearest-neighbour graph preparation, or base mapper configuration: [core embedding](../core-embedding/SKILL.md).
- Supervised label training, target metrics, densMAP semantics, or density interpretation: [supervised density](../supervised-density/SKILL.md).
- Parametric UMAP model/loss-history semantics: [parametric UMAP](../parametric-umap/SKILL.md). Plotting mechanics for an already fitted 2D mapper can route back here.

## First Checks

1. Confirm the mapper is fitted and exposes `embedding_` or `embedding`.
2. Confirm the plotted embedding is 2D.
3. Confirm `labels`, `values`, `subset_points`, and `hover_data` align to plotted rows.
4. Treat plot extras as optional. Base UMAP does not require `umap.plot`.
5. Run [`scripts/check_plotting_stack.py`](scripts/check_plotting_stack.py) before debugging optional plotting failures.

## Recovery Path

1. If `import umap.plot` fails, install `umap-learn[plot]` or the conda package set in [plotting reference](references/plotting-reference.md).
2. If plot extras are unavailable, fall back to `mapper.embedding_` and plain matplotlib or export the embedding for plotting elsewhere.
3. For static and datashaded plots, read [plotting reference](references/plotting-reference.md) for API contracts and row-alignment rules.
4. For errors, display confusion, hover/search mismatches, or performance issues, read [troubleshooting](references/troubleshooting.md).

## Display Rules

- Use `umap.plot.output_notebook()` before interactive notebook display.
- Use `umap.plot.output_file("plot.html")` before interactive file output.
- Use `umap.plot.show(plot_to_show)` on the object returned by `interactive` or on a matplotlib axis when you want the package display helper.
