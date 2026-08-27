---
name: themes-palettes
description: "Use seaborn theme, style, context, palette, colormap, color
  utility, and optional interactive palette widget APIs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Themes and Palettes

Use this sub-skill when the task asks about seaborn aesthetics, `set_theme`, `axes_style`, `plotting_context`, `color_palette`, palette generation, colormaps, dark mode, or interactive palette widgets.

## Route Here For

- Setting global defaults with `set_theme`, `set`, `set_style`, `set_context`, or `set_palette`.
- Temporary styles with `axes_style`, `plotting_context`, and `color_palette` context managers.
- Choosing categorical palettes, sequential/diverging colormaps, cubehelix, HLS/HUSL, blend/dark/light palettes, xkcd/crayon colors, or matplotlib palettes.
- Visualizing palettes with `palplot`.
- Color helper functions: `desaturate`, `saturate`, `set_hls_values`.
- Optional interactive chooser functions that require `ipywidgets`.

## Use Another Sub-skill For

- Plot family parameter choices: `../function-interface/SKILL.md`.
- Objects property mapping and scale objects: `../objects-interface/SKILL.md`.
- Figure/grid sizing or legends: `../figure-grids/SKILL.md`.

## Start With

1. Decide whether the color variable is categorical, sequential numeric, or diverging around a meaningful center.
2. Choose a palette/colormap that matches the data semantics and output background.
3. Use context managers for temporary style/palette changes; use `set_theme` for notebook/session defaults.
4. Validate palette length and colormap behavior before using it in a complex plot.
5. Treat widget choosers as optional notebook-only tools.

## References

- Theme and palette API map: `references/api-reference.md`.
- Palette/style recipes: `references/workflows.md`.
- Failure recovery: `references/troubleshooting.md`.

## Quick Smoke Check

```bash
python sub-skills/themes-palettes/scripts/theme_palette_smoke.py --output theme_palette_smoke.png
```
