---
name: visualization-jupyter
description: "Create Vaex histograms, heatmaps, scatter plots, expression plots,
  saved Matplotlib outputs, and high-level Jupyter widget workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# visualization-jupyter

Use this sub-skill when the task is to plot or explore Vaex data with `df.viz` / `expression.viz`, save Matplotlib output, or work with Vaex's Jupyter widget layer. If the task still needs DataFrame creation, inspection, filtering, or basic lazy semantics before plotting, route that part to `../dataframe-core/SKILL.md`. Keep plotting and display separate: if the user needs custom counts, means, correlations, binning, groupby grids, or other precomputed statistics behind a plot, route that work to `../expressions-analytics/SKILL.md`; if the user needs REST plot endpoints or remote plot serving, route it to `../serving-remote/SKILL.md`.

## Load these references

- [references/visualization-workflows.md](references/visualization-workflows.md)
- [references/jupyter-widgets.md](references/jupyter-widgets.md)
- [references/troubleshooting.md](references/troubleshooting.md)
- [scripts/plot_smoke.py](scripts/plot_smoke.py)

## Core operating rules

1. Use `df.viz.histogram`, `df.viz.heatmap`, `df.viz.scatter`, and `expression.viz.histogram` for plotting. Treat `df.plot1d` and direct `df.scatter` / `df.plot` aliases as compatibility shims that may warn; prefer the `df.viz` namespace in new guidance.
2. Keep analytics separate from presentation. If the task asks for custom counts, means, correlations, binning, groupby grids, or other precomputed statistics behind a plot, send that part to `../expressions-analytics/SKILL.md` and use this sub-skill only for rendering or display choices.
3. For saved figures or CI/server smoke checks, use Matplotlib with the `Agg` backend and `show=False`. Use `hardcopy=` on histogram/heatmap when possible; for scatter, save the current figure explicitly after plotting. Do not require a notebook frontend for terminal checks.
4. Use `selection`, `limits`, `shape`, `what`, `f`, `normalize_axis`, and facet-style syntax as plotting controls. Treat `what` as a small expression language such as `count(*)`, `mean(x)`, `sum(x)`, `std(x)`, or `correlation(a, b)`; if the syntax does not parse, fall back to the troubleshooting reference.
5. Use `df.viz.scatter` only for small DataFrames or explicitly bounded selections. If the row count is large, choose histogram/heatmap with aggregated grids instead of eager scatter plotting.
6. For Jupyter, use `df.widget` accessors at a high level: `histogram`, `heatmap`, `data_array`, `expression`, `column`, `selection_expression`, and progress widgets. Treat `bqplot`, `ipyvolume`, `ipyleaflet`, `ipympl`, `ipyvuetify`, `ipywidgets`, and `xarray` as frontend dependencies that may be present or absent.
7. For progress feedback, prefer simple progress, `progress='widget'` in notebook contexts, or rich tree progress when you need nested task detail. Keep the choice consistent with the execution environment.

## Reference map

- `references/visualization-workflows.md`: plotting recipes, expression plots, `hardcopy`/`show`, facets, and display-vs-computation guidance.
- `references/jupyter-widgets.md`: `df.widget` concepts, widget stack, interactive plot patterns, and frontend behavior.
- `references/troubleshooting.md`: deprecation warnings, invalid `what`/facet syntax, scatter row limits, headless display errors, missing Matplotlib or frontend packages, and progressbar mismatches.

## Bundled check

Run the bundled smoke check after editing this sub-skill or when diagnosing an environment:

```bash
python scripts/plot_smoke.py --help
python scripts/plot_smoke.py
```

The script creates tiny in-memory data only, uses public Vaex APIs, writes noninteractive Matplotlib PNGs with the `Agg` backend, and asserts that each saved file is non-empty.
