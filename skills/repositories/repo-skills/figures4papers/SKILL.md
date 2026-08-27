---
name: figures4papers
description: "Create, polish, and troubleshoot figures4papers-style
  publication-ready matplotlib figures, including grouped bars, trends, radar
  charts, heatmaps, concept diagrams, manifolds, and high-DPI/vector export
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# figures4papers

Use this repo skill when the user wants publication-quality Python/matplotlib
figures in the figures4papers house style: polished paper plots, wide comparison
panels, print-safe encodings, radar or heatmap layouts, conceptual manifolds,
clean typography, and reproducible PNG/PDF/SVG export.

This repository is a script-and-skill collection, not an installable Python
package. Future agents can use this generated skill without the original
checkout by following the bundled references and scripts below.

## Load this skill when

- The user asks for a paper, slide, or report figure rather than exploratory
  data analysis.
- The figure should use a consistent publication look: sans-serif typography,
  blue/green/red/neutral palette roles, clean spines, high DPI, and vector text.
- The request mentions grouped bars, ablations, wide metric comparisons,
  legend-only axes, trend lines, event timelines, radar/polar comparisons,
  heatmaps, matrix panels, concept distributions, manifolds, Swiss-roll
  diffusion visuals, shaded spheres, or geodesic/arrow diagrams.
- The user needs to adapt a safe template, validate data shapes, create output
  directories, or fix matplotlib font, TeX, backend, or export errors.
- The task names figures4papers or asks for the same style as a figures4papers
  example.

## Do not load for

- Interactive dashboards or web visualization with Plotly, Altair, Bokeh, or
  dashboard frameworks.
- GIS/geographic mapping, Figma/Illustrator-first infographic work, or purely
  exploratory plots without a publication target.
- Model training, data analysis, evaluation, or paper reproduction where plotting
  is incidental rather than the requested deliverable.
- Exact historical figure reproduction that would require unbundled data or
  source files. Use the distilled recipes and ask for user-provided data instead.

## Minimal environment

Install the plotting packages needed by the selected route:

```bash
python -m pip install numpy matplotlib scipy seaborn python-dateutil
```

`numpy` and `matplotlib` cover the core templates. `scipy` supports KDE,
diffusion, and manifold helpers; `seaborn` supports seaborn-style heatmaps;
`python-dateutil` helps date/month timelines. System LaTeX is optional and only
needed when exact `text.usetex=True` rendering is required. Portable bundled
scripts keep TeX disabled by default.

Run the environment checker when import or export behavior is uncertain:

```bash
python scripts/check_figure_env.py --output figure_env_smoke --formats png
```

## Route map

| Task | Open |
| --- | --- |
| Grouped bars, horizontal ablations, log-speed bars, multi-metric comparison rows, direct annotations, legend-only axes | [sub-skills/bar-comparison-figures/SKILL.md](sub-skills/bar-comparison-figures/SKILL.md) |
| Trend/line panels, cumulative timelines, event arrows, radar/polar benchmark comparisons, heatmaps, colorbars, matrix panels | [sub-skills/trend-radar-heatmap-figures/SKILL.md](sub-skills/trend-radar-heatmap-figures/SKILL.md) |
| Concept distributions, manifold clouds, KDE contours, Swiss-roll/diffusion matrices, shaded spheres, geodesic arrows, 3D-style geometry | [sub-skills/concept-manifold-diagrams/SKILL.md](sub-skills/concept-manifold-diagrams/SKILL.md) |
| Shared style, palette, rcParams, export formats, and helper functions | [references/style-and-export.md](references/style-and-export.md) |
| Natural-language pattern routing across all figure families | [references/project-patterns.md](references/project-patterns.md) |
| Cross-cutting install/import, font, TeX, backend, shape, and output failures | [references/troubleshooting.md](references/troubleshooting.md) |
| Repository snapshot and refresh baseline | [references/repo-provenance.md](references/repo-provenance.md) |

## Shared scripts

- [scripts/figure_style_helpers.py](scripts/figure_style_helpers.py) provides
  reusable palette constants, `FigureStyle`, `apply_publication_style`,
  `create_subplots`, `finalize_figure`, grouped bar, trend, heatmap, scatter,
  and shaded-sphere helpers.
- [scripts/check_figure_env.py](scripts/check_figure_env.py) verifies required
  plotting imports, optional dependencies, LaTeX availability, and headless PNG
  export.

## Operating procedure

1. Classify the figure family from the route map before writing code.
2. Read the nearest sub-skill and its recipe reference; use the bundled template
   when the user has not provided a mature plotting script.
3. Normalize user data into the sub-skill's data contract and validate shapes,
   label counts, finite values, metric directions, and missing-value policy.
4. Apply the shared style: semantic palette roles, clean spines, readable fonts,
   frameless legends, print-safe edges/hatches where needed, and TeX off unless
   explicitly required.
5. Save deterministic outputs in the requested formats, create parent
   directories, close figures, and verify nonzero file sizes.
6. If a failure appears, use root troubleshooting first, then the owning
   sub-skill's troubleshooting reference for workflow-specific recovery.

## Ask before finalizing when

- The metric direction, missing-value policy, or synthetic-vs-measured status is
  unclear.
- A tight axis range could be misleading or a zero baseline may be required.
- The user did not specify mandatory figure dimensions, formats, DPI, or venue
  constraints and those choices affect layout.
- Exact TeX rendering or a specific font is required but not available.
- A requested composite figure spans several sub-skills and the panel order or
  story should be user-approved.

## Refresh and import notes

Read [references/repo-provenance.md](references/repo-provenance.md) before
refreshing this skill against a changed repository. This candidate was generated
for DisCo's managed repo-skill format, but this construction run intentionally
does not import it into the live repo-skills library.
