# Style and Export Reference

Read this when a figures4papers task needs shared palette, typography, rcParams, output formats, or portable publication defaults before choosing a specific sub-skill.

## House style summary

The figures4papers style is minimalist, high-contrast, and publication-oriented:

- White background; top and right spines removed for ordinary axes.
- Sans-serif typography with a portable fallback. Use DejaVu Sans by default in reusable scripts, and switch to Arial/Helvetica only when available and required by the target venue.
- Large readable labels: 16-18 pt for compact panels, 22-24 pt for large bar rows, and smaller annotation fonts only when cell/bar density requires it.
- Frameless legends; move long legends into a dedicated legend axis or outside the data axes.
- Strong black bar edges or line widths when grayscale print readability matters.
- Deterministic outputs from the same figure object, usually PNG plus PDF.

## Palette

Use semantic color roles instead of arbitrary palettes.

| Role | Color | Use |
| --- | --- | --- |
| Key/proposed | `#0F4D92` | Main method, target manifold, primary trend |
| Secondary blue | `#3775BA` | Related target or supporting blue series |
| Positive family | `#DDF3DE`, `#AADCA9`, `#8BCF8B` | Improvements, additive variants, supporting positives |
| Contrast family | `#F6CFCB`, `#E9A6A1`, `#B64342` | Baselines, negative contrasts, arrows/forces |
| Neutral family | `#CFCECE`, `#767676`, `#4D4D4D` | Background methods, prior manifolds, reference groups |
| Accent | `#FFD700`, `#42949E`, `#9A4D8E` | One-off callouts, teal/violet secondary geometry |

Do not use too many accents in one figure. If color roles exceed the palette, add hatches, line styles, marker shapes, or panel separation before inventing new colors.

## rcParams baseline

For portable scripts:

```python
import matplotlib
matplotlib.use("Agg")  # before importing pyplot in unattended runs
import matplotlib.pyplot as plt

plt.rcParams.update({
    "font.family": ["DejaVu Sans", "Arial", "Helvetica", "sans-serif"],
    "font.size": 16,
    "axes.spines.right": False,
    "axes.spines.top": False,
    "axes.linewidth": 2.5,
    "legend.frameon": False,
    "svg.fonttype": "none",
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "figure.facecolor": "white",
    "savefig.facecolor": "white",
})
```

Use `text.usetex=True` only when the runtime has LaTeX and exact TeX rendering is required. The portable default is TeX off with matplotlib mathtext and Unicode arrows such as `↑` or `↓`.

## Export policy

- Use PNG at 300 DPI for ordinary panels.
- Use 600 DPI for very dense bar panels or raster-heavy figures when vector output is not appropriate.
- Save PDF or SVG for line art, text, vector bars, and diagrams that will be edited in a paper workflow.
- Create parent directories before saving.
- Save all requested formats before closing the figure.
- Check that each output file exists and has nonzero size.

A safe save helper should treat an output path without a known suffix as a basename and add each requested format. If the user passes `figure.png` plus `formats=["pdf"]`, strip the suffix and save `figure.pdf` rather than creating `figure.png.pdf`.

## Choosing sub-skills

- Use `bar-comparison-figures` for grouped bars, ablations, log-speed bars, multi-metric comparison rows, direct bar annotations, and legend-only axes.
- Use `trend-radar-heatmap-figures` for line/trend panels, event timelines, radar/polar benchmark comparisons, heatmaps, colorbars, and matrix-style result panels.
- Use `concept-manifold-diagrams` for conceptual distributions, point-cloud manifolds, diffusion matrices, shaded spheres, geodesic arrows, and schematic geometry.

## Bundled helpers

- Use [`../scripts/figure_style_helpers.py`](../scripts/figure_style_helpers.py) as a reusable helper module when a task benefits from shared style, validation, and export utilities.
- Run [`../scripts/check_figure_env.py`](../scripts/check_figure_env.py) when a user's environment may be missing matplotlib, numpy, optional SciPy/seaborn/dateutil, LaTeX, or headless export support.
