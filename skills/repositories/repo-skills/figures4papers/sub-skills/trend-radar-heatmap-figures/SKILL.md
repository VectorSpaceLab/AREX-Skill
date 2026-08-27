---
name: trend-radar-heatmap-figures
description: "Build publication-ready trend panels, event-annotated cumulative
  time series, normalized radar comparisons, heatmaps, matrix panels, and shared
  legends."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# Trend, Radar, and Heatmap Figures

Use this sub-skill when a figures4papers task asks for publication-ready matplotlib figures involving line or sweep curves, cumulative time series, event annotations, radar/polar benchmark comparisons, seaborn or matplotlib heatmaps, matrix-style comparison panels, colorbars, per-cell labels, or shared/legend-only layouts.

## Route here for

- Line, sweep, post-training, or ablation curves with 2-4 readable series per axis.
- Cumulative time-series panels with parsed month/date labels, filled areas, hatch overlays, and event arrows.
- Radar or polar benchmark comparisons where each spoke has its own natural score scale and tick labels.
- Heatmaps with row/column totals, colorbars, annotations, per-cell text contrast, or summary/improvement rows.
- Wide comparison panels that mix trends, heatmaps, matrix blocks, and a dedicated shared-legend axis.

## Route elsewhere

- Grouped bars, horizontal ablation bars, log bars, or print-safe bar comparisons: use `bar-comparison-figures`.
- Conceptual manifolds, spheres, scatter clouds, KDE contours, Swiss-roll diagrams, or schematic arrows: use `concept-manifold-diagrams`.
- Cross-cutting palette, font, export, and environment helpers: use the root figures4papers references/scripts when they are available; this sub-skill does not require them.

## Read or run

- Read [references/trend-radar-heatmap-recipes.md](references/trend-radar-heatmap-recipes.md) before implementing any trend, radar, heatmap, matrix, colorbar, or shared-legend figure. It contains the data contracts, normalization formulas, date/event handling, layout recipes, and output validation checklist.
- Read [references/troubleshooting.md](references/troubleshooting.md) when the figure has shape mismatches, date/event problems, malformed radar polygons, bad tick labels, unreadable heatmap text, colorbar issues, optional TeX/seaborn failures, or missing output files.
- Run [scripts/trend_radar_heatmap_template.py](scripts/trend_radar_heatmap_template.py) to create safe built-in examples for `--example trend`, `--example radar`, or `--example heatmap`. Use it as a self-contained starting point when no project-specific plotting code exists.

## Operating checklist

1. Identify the figure family: trend/event, radar, heatmap, matrix panel, or mixed layout.
2. Validate the data contract from the recipes before plotting: array rank, label counts, method/order alignment, finite numeric values, and date coverage.
3. Keep figures self-contained and headless-friendly: no network, credentials, hidden global state, or dependence on external source checkouts.
4. Prefer non-TeX defaults. Enable TeX only when the runtime explicitly has a LaTeX installation and the target venue requires TeX-rendered labels.
5. Save with deterministic output names and verify that every requested file exists, is non-empty, and can be opened by matplotlib/Pillow or a simple file-size check.
