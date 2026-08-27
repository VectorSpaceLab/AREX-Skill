# Project Pattern Map

Read this to map a natural figure request to the right figures4papers workflow family. This is a distilled runtime map; it does not require opening the source repository.

## Pattern families

| User asks for | Best route | Typical inputs | Output expectations |
| --- | --- | --- | --- |
| Method comparison bars across metrics | `sub-skills/bar-comparison-figures/` | Methods, metrics, means, optional errors, colors | Wide row of metric panels plus legend-only axis, PNG/PDF |
| Ablation component bars | `sub-skills/bar-comparison-figures/` | Variants, component labels or binary codes, metrics, errors | Horizontal or vertical ablation panels, decoded labels, tight limits |
| Log-scale speed/throughput comparison | `sub-skills/bar-comparison-figures/` | Positive times or rates, method labels | Log bars, no zero values, annotations above bars |
| Multi-series trends or sweeps | `sub-skills/trend-radar-heatmap-figures/` | X values, one array per series, labels, optional uncertainty | Line panels with shared colors and readable legend |
| Cumulative timeline with event labels | `sub-skills/trend-radar-heatmap-figures/` | Date/month labels, increments or cumulative counts, events | Filled trends, event arrows, sparse ticks |
| Radar comparison across benchmarks | `sub-skills/trend-radar-heatmap-figures/` | Methods, spokes, values, per-spoke ranges/ticks | Closed polygons, custom spokes, natural tick labels per axis |
| Heatmap or matrix result panel | `sub-skills/trend-radar-heatmap-figures/` | 2D matrix, row/column labels, color scale | Annotated cells, contrast-aware text, colorbar |
| Concept distribution or probability sketch | `sub-skills/concept-manifold-diagrams/` | Curves or synthetic parameters, target marker, labels | Smooth curves, fills, arrows, clear synthetic/result distinction |
| Manifold/latent-space concept diagram | `sub-skills/concept-manifold-diagrams/` | Point clouds, ridges, optional KDE contours | Low-alpha clouds, contour/ridge overlays, axis cleanup |
| Swiss-roll/diffusion visualization | `sub-skills/concept-manifold-diagrams/` | Points, ordering parameter, kernel/threshold | Transition matrix plus point cloud, normalized rows |
| Sphere/geodesic/3D geometry sketch | `sub-skills/concept-manifold-diagrams/` | Synthetic points, arrows, labels, light direction | Shaded sphere or 3D-like panel, clean arrows, axis-free layout |

## Decision points to clarify

Ask the user before finalizing only when the choice affects figure semantics or publication constraints:

- Metric direction: higher-is-better, lower-is-better, or signed improvement.
- Whether values are measured results or illustrative synthetic data.
- Whether a zero baseline must remain visible when tight y-limits would make differences clearer.
- Required output formats, dimensions, DPI, or venue constraints.
- Whether exact TeX rendering is mandatory; portable scripts default to non-TeX.
- Whether missing values should be imputed, dropped, or shown explicitly.
- Whether a single composite panel or separate figures are needed.

## Source idioms preserved in bundled outputs

The generated skill preserves reusable idioms rather than paper-specific hardcoded values:

- Legend-only axes for crowded comparison figures.
- Wide canvases for multi-metric comparison rows.
- Tight dynamic limits for high-range scores.
- Hatches, black edges, and alpha gradients for print-safe bars.
- Per-spoke radar normalization with custom tick labels.
- Cumulative trends with event arrows and sparse date ticks.
- Heatmap annotation colors chosen from rendered luminance.
- Deterministic synthetic manifolds, diffusion matrices, and sphere shading.

Use the bundled templates when a new figure needs a safe starting point:

- `sub-skills/bar-comparison-figures/scripts/bar_comparison_template.py`
- `sub-skills/trend-radar-heatmap-figures/scripts/trend_radar_heatmap_template.py`
- `sub-skills/concept-manifold-diagrams/scripts/concept_manifold_template.py`
