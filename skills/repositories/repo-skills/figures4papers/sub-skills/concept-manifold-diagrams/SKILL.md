---
name: concept-manifold-diagrams
description: "Create publication-ready conceptual scientific diagrams with
  scatter clouds, KDE contours, manifold curves, Swiss-roll diffusion matrices,
  shaded spheres, geodesic arrows, and 3D projection arrows in the
  figures4papers style."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# Concept Manifold Diagrams

Use this sub-skill when the requested figure is a **conceptual diagram** rather than a quantitative result plot: concept distributions, latent/manifold geometry, diffusion or transition structure, sphere/geodesic illustrations, or projection/repulsion arrows.

## Route here for

- VIGIL-style concept distributions: overlapping probability curves, highlighted target gaps, and a paired conceptual manifold panel.
- Cflows-style Swiss-roll or diffusion visuals: ordered transition/probability matrices beside manifold point clouds and local connections.
- Dispersion-style geometry diagrams: shaded 2D spheres, sampled points, radial guides, geodesic arcs, directional arrows, and 3D projection/repulsion arrows.
- RNAGenScape-style manifolds: smooth synthetic energy surfaces, multi-well landscapes, and hole/constraint overlays.

## Route elsewhere

- Ordinary quantitative bars, grouped comparisons, horizontal ablations, value annotations, or legend-only bar panels: use `bar-comparison-figures`.
- Radar charts, trend/line panels, event timelines, heatmaps, or matrix result comparisons: use `trend-radar-heatmap-figures`.
- Cross-cutting palette, export, environment, or shared helper concerns: use the root `figures4papers` references/scripts once available.

## Operating workflow

1. Decide whether the diagram is **synthetic explanatory geometry** or a **data-backed result plot**. This sub-skill is for the former; do not imply synthetic samples are measured results.
2. Read [`references/concept-manifold-recipes.md`](references/concept-manifold-recipes.md) for the recipe matching the requested visual family:
   - probability/distribution panels,
   - scatter clouds with KDE contours and manifold ridges,
   - Swiss-roll plus diffusion matrix,
   - 3D manifold and hole surfaces,
   - shaded spheres, geodesic arcs, and projection arrows.
3. Run or adapt [`scripts/concept_manifold_template.py`](scripts/concept_manifold_template.py) when a safe starting script is useful. It is self-contained, deterministic, headless-friendly, and creates figures from built-in synthetic data:
   - `python scripts/concept_manifold_template.py --example distribution --output concept_distribution`
   - `python scripts/concept_manifold_template.py --example manifold --output manifold_surface --formats png,pdf`
   - `python scripts/concept_manifold_template.py --example swiss-roll --output swiss_roll`
   - `python scripts/concept_manifold_template.py --example sphere --output sphere_geometry`
4. Before final export, apply the validation checklist in the recipes: deterministic seed, finite sample/grid sizes, normalized probability rows where applicable, visible arrows/text, clean axes, and PNG/PDF output at publication DPI.
5. If SciPy, KDE, matrix normalization, TeX labels, 3D arrows, or layout fail, read [`references/troubleshooting.md`](references/troubleshooting.md) before changing the figure design.

## Style expectations

- Use the figures4papers house look: minimalist axes, large sans-serif labels, blue/neutral/red semantic palette, white backgrounds, dense-but-readable panels, and 300 DPI exports.
- Prefer annotations, arrows, and legend-only cues over heavy grids for conceptual diagrams.
- Keep stochastic visuals reproducible with explicit seeds and note that all generated template examples are illustrative synthetic data.
