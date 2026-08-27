---
name: bar-comparison-figures
description: "Design publication-ready grouped, ablation, and multi-metric bar
  comparison figures in the figures4papers house style."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# Bar Comparison Figures

This sub-skill routes bar-oriented publication figure requests inside the
`figures4papers` operating graph. Use it when the user needs grouped bars,
wide comparison panels, method ablations, direct value labels, error bars,
print-safe fills, or a legend-only axis in a matplotlib figure.

## Load this sub-skill when

- The requested figure compares methods, datasets, prompts, variants, or
  ablation components with vertical or horizontal bars.
- The user asks for wide multi-metric panels with one metric per axis and a
  shared method legend.
- The user needs direct numeric annotations above bars or inside bars.
- The data include means with standard deviations, standard errors, confidence
  intervals, or other symmetric bar errors.
- The plot should hide dense method names from the x-axis and identify them via
  a legend-only panel.
- Ablation variants are naturally displayed with `barh`, component labels, or
  binary component codes decoded into readable names.
- The chart must stay readable in grayscale print by combining palette roles,
  dark edges, hatches, and alpha gradients.
- The user needs deterministic, high-DPI PNG/PDF output from a headless script.

## Route away when

- Radar, polar, trend-line, cumulative-event, sweep-curve, heatmap, or matrix
  comparison workflows are better handled by `trend-radar-heatmap-figures`.
- Conceptual scatter clouds, manifolds, spheres, Swiss-roll panels, arrows, or
  explanatory diagrams are better handled by `concept-manifold-diagrams`.
- The task is only to set global style constants, inspect matplotlib/backends,
  or check optional LaTeX; those cross-cutting checks belong at the root.
- The user asks to exactly reproduce a historical repository figure; provide a
  self-contained distilled recipe instead of pointing to source checkout files.

## Fast routing checklist

1. Identify the comparison unit: method, model, prompt, dataset, ablation row,
   or metric.
2. Decide the bar geometry: vertical method bars, grouped method-by-category
   bars, stacked subtype bars, or horizontal ablation bars.
3. Decide panel structure: single axis, one axis per metric, one axis per
   dataset, or data axes plus one legend-only axis.
4. Determine whether exact numbers should be annotated and where those labels
   fit without colliding with error bars.
5. Choose a semantic encoding: blue for the proposed/key method, greens for
   related positives, reds/pinks for contrasts, neutrals for baselines.
6. Add black bar edges and hatches when the palette alone is insufficient for
   grayscale or print-safe reading.
7. Set dynamic y-limits or x-limits from the data rather than using a generic
   0-1 or 0-100 range when differences are narrow.
8. Export to the requested formats at high DPI, creating parent directories and
   closing the figure after saving.

## Reference and script map

- Read [references/bar-recipes.md](references/bar-recipes.md) for concrete data
  schemas, grouped bar recipes, horizontal ablation recipes, legend-only panel
  construction, annotation placement, y-limit heuristics, print-safe encodings,
  and export checks.
- Read [references/troubleshooting.md](references/troubleshooting.md) when a bar
  figure has mismatched array shapes, misplaced labels, crowded legends,
  ambiguous color/hatch encodings, optional TeX failures, missing fonts, or
  output-directory problems.
- Run or adapt [scripts/bar_comparison_template.py](scripts/bar_comparison_template.py)
  when the user needs a safe starting script. It contains built-in example data
  for `--example grouped` and `--example horizontal-ablation`, supports PNG/PDF
  export, and validates shape mismatches before drawing.

## Operating procedure

1. Restate the requested comparison in terms of a compact table: rows are
   methods or ablations, columns are metrics or conditions, and optional arrays
   carry errors.
2. If the user provides long method names, put names in a legend-only panel or
   a wrapped y-axis for horizontal bars rather than rotating dozens of x labels.
3. If there are three or more metrics, prefer a wide row of panels with shared
   colors and one legend axis.
4. If values occupy a tight interval such as 0.82-0.91, tighten the axis to show
   differences while preserving enough margin for annotations and error caps.
5. If zero is scientifically meaningful or the venue expects absolute baselines,
   keep zero visible and explain that the visual contrast is intentionally lower.
6. Place numeric labels above vertical bars when error bars are present; place
   them inside bars only when contrast is strong and no error cap is hidden.
7. For horizontal ablations, keep component labels only on the first metric axis
   and hide repeated y tick labels on the remaining axes.
8. Use alpha gradients for ordered ablation completeness, hatches for subtypes,
   and black edges for all print-sensitive bars.
9. Use log scale only for strictly positive throughput or speed comparisons;
   annotate log bars multiplicatively above each bar, never below zero.
10. Create output directories automatically and save all requested formats from
    the same finalized figure.

## Expected observations

- Multi-metric bar figures appear as a clean left-to-right comparison with
  consistent colors across panels.
- Legends do not overlap bars because they live in a dedicated axis or outside
  the data region.
- Dense method names do not crowd the x-axis; ticks are hidden or abbreviated.
- Error bars have visible caps and do not cover annotation text.
- Tight y-limits emphasize meaningful performance differences without clipping
  labels or error caps.
- Bar fills remain distinguishable in grayscale through edges, hatches, or
  alpha differences.
- PNG/PDF outputs are deterministic and generated without network access.

## Stop and ask when

- The user has not specified whether a metric is higher-is-better or
  lower-is-better and the direction affects labels, sorting, or callouts.
- The requested layout could be either a single grouped axis or a multi-panel
  metric row and the publication space is constrained.
- A log-scale speed panel contains zero or negative values.
- Exact venue dimensions, export formats, or DPI are mandatory but missing.
- The data table has ambiguous missing values that should not be silently
  imputed or dropped.

## Handoff notes for future agents

- Keep generated scripts self-contained; do not rely on historical source files.
- Keep detailed recipes in references and keep this file as the router.
- Prefer reproducible sample data or user-provided tables over hardcoded paper
  values copied from examples.
- For difficult failures, first run the bundled template with built-in examples
  to separate environment/export issues from user-data issues.
